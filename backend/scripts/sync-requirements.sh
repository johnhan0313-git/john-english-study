#!/usr/bin/env bash
# Regenerate requirements.txt from pyproject.toml dependencies.
# Usage: ./scripts/sync-requirements.sh
set -euo pipefail
cd "$(dirname "$0")/.."

HEADER="# Sync with pyproject.toml — run scripts/sync-requirements.sh to refresh"
DEPS=(
  "fastapi>=0.115.0"
  "uvicorn[standard]>=0.32.0"
  "sqlalchemy>=2.0.36"
  "alembic>=1.14.0"
  "pydantic>=2.10.0"
  "pydantic-settings>=2.6.0"
  "httpx>=0.28.0"
  "apscheduler>=3.10.4"
  "python-multipart>=0.0.17"
  "python-jose[cryptography]>=3.3.0"
  "passlib[bcrypt]>=1.7.4"
  "edge-tts>=6.1.0"
  "eval_type_backport>=0.2.0"
  "pytest>=8.3.0"
  "pytest-asyncio>=0.24.0"
)

{
  echo "$HEADER"
  printf '%s\n' "${DEPS[@]}"
} > requirements.txt

echo "Wrote requirements.txt (${#DEPS[@]} packages)"
