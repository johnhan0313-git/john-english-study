#!/usr/bin/env bash
# 通过 rsync + docker compose 部署到 john-server，绕过 Portainer 每次从 GitHub clone。
# 用法：./scripts/deploy-john-server.sh
# 首次需在服务器创建 ~/apps/john-english-study/.env.prod（见 docs/PORTAINER_DEPLOY.md）

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REMOTE="${JOHN_SERVER:-john-server}"
REMOTE_DIR="${REMOTE_DIR:-/home/john-han/apps/john-english-study}"
ENV_FILE="${ENV_FILE:-.env.prod}"

echo "→ rsync to ${REMOTE}:${REMOTE_DIR}"
ssh "${REMOTE}" "mkdir -p '${REMOTE_DIR}'"
rsync -avz --delete \
  --exclude .git \
  --exclude node_modules \
  --exclude apps/web/.next \
  --exclude backend/.venv \
  --exclude backend/__pycache__ \
  --exclude backend/.env \
  --exclude .env.prod \
  --exclude '**/__pycache__' \
  --exclude '.cursor' \
  "${ROOT}/" "${REMOTE}:${REMOTE_DIR}/"

echo "→ docker compose up --build"
ssh "${REMOTE}" bash -s <<EOF
set -euo pipefail
cd "${REMOTE_DIR}"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "缺少 ${REMOTE_DIR}/${ENV_FILE}，请参考 docs/PORTAINER_DEPLOY.md 创建" >&2
  exit 1
fi
docker compose --env-file "${ENV_FILE}" -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
EOF

echo "✓ 部署完成"
