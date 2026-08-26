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

# Audio ownership: only platform adapters may construct Audio / <audio>
if rg -n 'new Audio\(|<audio' \
  "$ROOT/packages/app-core/src/features" \
  "$ROOT/packages/app-core/src/app-chrome" \
  --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: features/app-chrome must not use new Audio or <audio>; use PlatformServices.audio"
  rg -n 'new Audio\(|<audio' \
    "$ROOT/packages/app-core/src/features" \
    "$ROOT/packages/app-core/src/app-chrome" \
    --glob '*.{ts,tsx}' || true
  fail=1
fi

# Auth public API: chrome/platform should import from features/auth index, not deep ui paths
if rg -n 'from ["'\'']\.\./features/auth/(ui|auth-context|token)' \
  "$ROOT/packages/app-core/src/app-chrome" \
  "$ROOT/packages/app-core/src/platform" \
  --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: app-chrome/platform must import auth via features/auth public API"
  rg -n 'from ["'\'']\.\./features/auth/(ui|auth-context|token)' \
    "$ROOT/packages/app-core/src/app-chrome" \
    "$ROOT/packages/app-core/src/platform" \
    --glob '*.{ts,tsx}' || true
  fail=1
fi

# Auth public API: features must not deep-import auth/ui or auth-context
if rg -n 'from ["'\''][^"'\'']*auth/(ui|auth-context)' \
  "$ROOT/packages/app-core/src/features" \
  --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: features must import auth via features/auth public API (not auth/ui or auth-context)"
  rg -n 'from ["'\''][^"'\'']*auth/(ui|auth-context)' \
    "$ROOT/packages/app-core/src/features" \
    --glob '*.{ts,tsx}' || true
  fail=1
fi

# Activity public API: app-chrome must use features/activity, not features/activity/model
if rg -n 'from ["'\''][^"'\'']*features/activity/model' \
  "$ROOT/packages/app-core/src/app-chrome" \
  --glob '*.{ts,tsx}' >/dev/null 2>&1; then
  echo "FAIL: app-chrome must import activity via features/activity public API"
  rg -n 'from ["'\''][^"'\'']*features/activity/model' \
    "$ROOT/packages/app-core/src/app-chrome" \
    --glob '*.{ts,tsx}' || true
  fail=1
fi

# api-client must not deep-export learning presentation helpers
if rg -n 'learning/' "$ROOT/packages/api-client/src/index.ts" >/dev/null 2>&1; then
  echo "FAIL: api-client must not export learning/* helpers"
  fail=1
fi

# Feature public indexes should not re-export internal learning/hooks trees
if rg -n 'export \* from ["'\'']\./ui/learning|export .* from ["'\'']\./hooks/' \
  "$ROOT/packages/app-core/src/features/activity/index.ts" \
  "$ROOT/packages/app-core/src/features/conversation/index.ts" >/dev/null 2>&1; then
  echo "FAIL: activity/conversation public API must not re-export learning internals or hooks"
  fail=1
fi

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
echo "Frontend architecture gates passed."
