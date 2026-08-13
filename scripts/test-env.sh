#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required. Install Docker Desktop or the docker-compose-plugin." >&2
  exit 1
fi
COMPOSE=(docker compose -f "$ROOT/docker-compose.test.yml")

cleanup() {
  "${COMPOSE[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

"${COMPOSE[@]}" build tests
"${COMPOSE[@]}" run --rm tests "$@"
