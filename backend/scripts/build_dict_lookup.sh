#!/usr/bin/env bash
# Import dictionary_entries from KyleBing/english-vocabulary into PostgreSQL.
# Run: ./scripts/build_dict_lookup.sh [--force]
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
if [[ "${1:-}" == "--force" ]]; then
  python -m app.cli seed-dictionary --force
else
  python -m app.cli seed-dictionary
fi
