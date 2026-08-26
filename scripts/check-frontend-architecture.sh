#!/usr/bin/env bash
# Frontend architecture gates for SceneEnglish monorepo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
fail=0

if [[ -d "$ROOT/apps/web/src/components" || -d "$ROOT/apps/web/src/lib" || -d "$ROOT/apps/web/src/hooks" ]]; then
  echo "FAIL: dead trees under apps/web/src (components/lib/hooks) must stay deleted"
  fail=1
fi

if rg -n '"\./pages/\*"|"\./components/\*"|"\./contexts/\*"' "$ROOT/packages/app-core/package.json" >/dev/null 2>&1; then
  echo "FAIL: app-core must not deep-export pages/components/contexts"
  fail=1
fi

if rg -n 'from "@sceneenglish/app-core/(pages|components|contexts)/' "$ROOT/apps" --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: hosts must not deep-import app-core pages/components/contexts"
  rg -n 'from "@sceneenglish/app-core/(pages|components|contexts)/' "$ROOT/apps" --glob '*.{ts,tsx}' || true
  fail=1
fi

if rg -n 'new MediaRecorder' "$ROOT/packages/app-core/src/features" --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: features must not construct MediaRecorder; use PlatformServices.recorder"
  rg -n 'new MediaRecorder' "$ROOT/packages/app-core/src/features" --glob '*.{ts,tsx}' || true
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "Frontend architecture gates passed."
