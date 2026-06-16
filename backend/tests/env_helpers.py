from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def _resolve_john_server_host(value: str) -> str:
    if "john-server" not in value:
        return value
    if not shutil.which("tailscale"):
        return value
    proc = subprocess.run(
        ["tailscale", "ip", "-4", "john-server"],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if proc.returncode != 0:
        return value
    ip = proc.stdout.strip().split("\n")[0]
    if ip:
        return value.replace("john-server", ip)
    return value


def load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ[key] = value


def load_backend_env() -> None:
    backend_dir = Path(__file__).resolve().parents[1]
    env_path = backend_dir / ".env"
    if not env_path.is_file():
        env_path = backend_dir / ".env.example"
    load_env_file(env_path)

    endpoint = os.environ.get("S3_ENDPOINT_URL", "")
    if endpoint:
        os.environ["S3_ENDPOINT_URL"] = _resolve_john_server_host(endpoint)


def assert_test_resource_isolation() -> None:
    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("postgresql"):
        db_name = db_url.rsplit("/", 1)[-1].split("?")[0]
        if db_name == "english-study":
            raise RuntimeError(
                "DATABASE_URL must not point to production database 'english-study'"
            )
        if db_name != "english-study-test":
            raise RuntimeError(
                f"Tests require database 'english-study-test', got '{db_name}'"
            )

    if os.environ.get("STORAGE_BACKEND", "") == "s3":
        bucket = os.environ.get("S3_BUCKET", "")
        if bucket == "english-study-bucket":
            raise RuntimeError("S3_BUCKET must not be production bucket 'english-study-bucket'")
        if bucket != "english-study-bucket-test":
            raise RuntimeError(
                f"Tests require bucket 'english-study-bucket-test', got '{bucket}'"
            )
