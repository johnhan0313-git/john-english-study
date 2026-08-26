"""Architecture gates for DDD dependency direction (migrated contexts)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

BACKEND_APP = Path(__file__).resolve().parents[1] / "app"

FORBIDDEN_DOMAIN_IMPORTS = {
    "sqlalchemy",
    "fastapi",
    "pydantic",
    "boto3",
    "app.database",
    "app.models",
    "app.infrastructure",
    "app.services",
    "app.api",
    "app.composition",
}


def _python_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.py"))


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0] if alias.name.startswith("app.") is False else alias.name)
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            mods.add(node.module.split(".")[0])
    return mods


def test_scenario_domain_has_no_forbidden_imports():
    domain_dir = BACKEND_APP / "domains" / "scenario"
    assert domain_dir.is_dir()
    for path in _python_files(domain_dir):
        if path.name == "__init__.py":
            continue
        imports = _imported_modules(path)
        for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
            assert not any(
                imp == forbidden or imp.startswith(forbidden + ".") for imp in imports
            ), f"{path} imports forbidden module matching {forbidden}: {imports}"


def test_progress_domain_has_no_forbidden_imports():
    domain_dir = BACKEND_APP / "domains" / "progress"
    assert domain_dir.is_dir()
    for path in _python_files(domain_dir):
        if path.name == "__init__.py":
            continue
        imports = _imported_modules(path)
        for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
            assert not any(
                imp == forbidden or imp.startswith(forbidden + ".") for imp in imports
            ), f"{path} imports forbidden module matching {forbidden}: {imports}"


def test_scenario_service_removed():
    assert not (BACKEND_APP / "services" / "scenario" / "service.py").exists()


def test_ensure_daily_and_tts_facade_removed():
    assert not (BACKEND_APP / "services" / "media" / "tts_facade.py").exists()
    # No ensure_daily_scenarios symbol in scenario package
    for path in _python_files(BACKEND_APP / "services" / "scenario"):
        text = path.read_text(encoding="utf-8")
        assert "ensure_daily_scenarios" not in text


def test_api_scenarios_does_not_construct_scenario_service():
    text = (BACKEND_APP / "api" / "scenarios.py").read_text(encoding="utf-8")
    assert "ScenarioService" not in text
    assert "get_container" in text or "AppContainer" in text


def test_repository_impl_does_not_commit():
    impl = BACKEND_APP / "infrastructure" / "persistence" / "scenario" / "scenario_repository_impl.py"
    text = impl.read_text(encoding="utf-8")
    assert ".commit(" not in text
    assert ".rollback(" not in text


def test_get_or_create_user_removed_from_auth_users():
    text = (BACKEND_APP / "auth" / "users.py").read_text(encoding="utf-8")
    assert "get_or_create_user" not in text
