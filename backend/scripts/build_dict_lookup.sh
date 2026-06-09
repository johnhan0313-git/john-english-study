#!/usr/bin/env bash
# Build backend/data/dict_lookup.json from KyleBing/english-vocabulary (educational use).
# Run: ./scripts/build_dict_lookup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
source .venv/bin/activate 2>/dev/null || true
python scripts/build_dict_lookup.py
