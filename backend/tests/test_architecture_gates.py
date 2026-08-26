"""Architecture gates for DDD dependency direction (migrated contexts)."""

from __future__ import annotations

import ast
from pathlib import Path

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

# Business routers that must not take Depends(get_db) after Application migration.
MIGRATED_API_MODULES = {
    "activity.py",
    "auth.py",
    "conversations.py",
    "exercises.py",
    "profile.py",
    "progress.py",
    "reference.py",
    "scenario_complete.py",
    "scenarios.py",
    "words.py",
}

MIGRATED_DOMAINS = ("scenario", "progress", "conversation")

# Services that have been replaced by Application (must not contain .commit().
MIGRATED_SERVICE_NO_COMMIT = (
    BACKEND_APP / "services" / "activity" / "service.py",
)


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
                mods.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
            mods.add(node.module.split(".")[0])
    return mods


def _assert_domain_clean(domain: str) -> None:
    domain_dir = BACKEND_APP / "domains" / domain
    assert domain_dir.is_dir(), f"missing domain {domain}"
    for path in _python_files(domain_dir):
        if path.name == "__init__.py":
            continue
        imports = _imported_modules(path)
        for forbidden in FORBIDDEN_DOMAIN_IMPORTS:
            assert not any(
                imp == forbidden or imp.startswith(forbidden + ".") for imp in imports
            ), f"{path} imports forbidden module matching {forbidden}: {imports}"


def test_migrated_domains_have_no_forbidden_imports():
    for domain in MIGRATED_DOMAINS:
        _assert_domain_clean(domain)


def test_scenario_service_removed():
    assert not (BACKEND_APP / "services" / "scenario" / "service.py").exists()


def test_conversation_service_removed():
    assert not (BACKEND_APP / "services" / "conversation" / "service.py").exists()


def test_auth_merge_module_removed():
    assert not (BACKEND_APP / "auth" / "merge.py").exists()


def test_ensure_daily_and_tts_facade_removed():
    assert not (BACKEND_APP / "services" / "media" / "tts_facade.py").exists()
    for path in _python_files(BACKEND_APP / "services" / "scenario"):
        text = path.read_text(encoding="utf-8")
        assert "ensure_daily_scenarios" not in text


def test_api_scenarios_does_not_construct_scenario_service():
    text = (BACKEND_APP / "api" / "scenarios.py").read_text(encoding="utf-8")
    assert "ScenarioService" not in text
    assert "get_container" in text or "AppContainer" in text


def test_api_conversations_uses_container():
    text = (BACKEND_APP / "api" / "conversations.py").read_text(encoding="utf-8")
    assert "ConversationService" not in text
    assert "get_container" in text
    assert "Depends(get_db)" not in text


def test_repository_impl_does_not_commit():
    roots = [
        BACKEND_APP / "infrastructure" / "persistence" / "scenario",
        BACKEND_APP / "infrastructure" / "persistence" / "progress",
        BACKEND_APP / "infrastructure" / "persistence" / "conversation",
    ]
    for root in roots:
        for path in _python_files(root):
            text = path.read_text(encoding="utf-8")
            assert ".commit(" not in text, f"{path} must not commit"
            assert ".rollback(" not in text, f"{path} must not rollback"


def test_migrated_services_do_not_commit():
    for path in MIGRATED_SERVICE_NO_COMMIT:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        assert ".commit(" not in text, f"{path} must not commit (Application owns UoW)"


def test_migrated_api_modules_do_not_use_get_db():
    api_dir = BACKEND_APP / "api"
    for name in MIGRATED_API_MODULES:
        path = api_dir / name
        assert path.exists(), f"missing api module {name}"
        text = path.read_text(encoding="utf-8")
        assert "Depends(get_db)" not in text, f"{path} still uses Depends(get_db)"
        assert "get_container" in text or name == "auth.py"


def test_get_or_create_user_removed_from_auth_users():
    text = (BACKEND_APP / "auth" / "users.py").read_text(encoding="utf-8")
    assert "get_or_create_user" not in text


def test_seed_helpers_avoid_ensure_prefix_for_tags():
    exam = (BACKEND_APP / "services" / "vocabulary" / "exam_tags.py").read_text(encoding="utf-8")
    assert "def ensure_exam_tag" not in exam
    assert "def apply_exam_tag" in exam
