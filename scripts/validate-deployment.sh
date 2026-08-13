#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${1:-$ROOT/.env.prod}"

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required for compose validation." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing production environment file: $ENV_FILE" >&2
  echo "Create it from .env.prod.example or export the variables in Portainer." >&2
  exit 1
fi

required=(DATABASE_URL S3_ACCESS_KEY S3_SECRET_KEY JWT_SECRET)
for key in "${required[@]}"; do
  value="$(sed -n "s/^${key}=//p" "$ENV_FILE" | tail -1)"
  if [[ -z "$value" || "$value" == *REPLACE_ME* || "$value" == change-me-in-production ]]; then
    echo "Invalid or missing $key in $ENV_FILE" >&2
    exit 1
  fi
done

jwt="$(sed -n 's/^JWT_SECRET=//p' "$ENV_FILE" | tail -1)"
if (( ${#jwt} < 32 )); then
  echo "JWT_SECRET must contain at least 32 characters" >&2
  exit 1
fi

secret_file="${GH_PACKAGES_TOKEN_FILE:-}"
cleanup_secret=0
if [[ -z "$secret_file" ]]; then
  secret_file="$(mktemp)"
  printf 'compose-validation-token' > "$secret_file"
  cleanup_secret=1
fi
cleanup() {
  if (( cleanup_secret )); then
    rm -f "$secret_file"
  fi
}
trap cleanup EXIT
GH_PACKAGES_TOKEN_FILE="$secret_file" docker compose --env-file "$ENV_FILE" -f "$ROOT/docker-compose.prod.yml" config --quiet
echo "Production compose and required environment values are valid."
