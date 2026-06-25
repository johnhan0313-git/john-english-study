#!/usr/bin/env bash
# john-server 一次性配置：所有 john-* 项目共用 GitHub Packages token（不必每个项目建 .env）
# 用法（在 john-server 上）:
#   echo 'ghp_xxxx' | ./scripts/setup-server-secrets.sh
#   GH_PACKAGES_TOKEN=ghp_xxxx ./scripts/setup-server-secrets.sh
set -euo pipefail

DIR="${GH_PACKAGES_TOKEN_DIR:-/home/john-han/.secrets}"
FILE="${GH_PACKAGES_TOKEN_FILE:-${DIR}/gh_packages_token}"
OWNER="${SUDO_USER:-${USER:-john-han}}"

mkdir -p "${DIR}"
chmod 700 "${DIR}"

if [[ -n "${GH_PACKAGES_TOKEN:-}" ]]; then
  TOKEN="${GH_PACKAGES_TOKEN}"
elif [[ ! -t 0 ]]; then
  read -r TOKEN
else
  echo "请设置 GH_PACKAGES_TOKEN 或 pipe token: echo 'ghp_...' | $0" >&2
  exit 1
fi

if [[ -z "${TOKEN}" ]]; then
  echo "错误: token 为空" >&2
  exit 1
fi

printf '%s' "${TOKEN}" > "${FILE}"
chmod 600 "${FILE}"
chown "${OWNER}:${OWNER}" "${FILE}" 2>/dev/null || true
chown "${OWNER}:${OWNER}" "${DIR}" 2>/dev/null || true
chmod 700 "${DIR}" 2>/dev/null || true
echo "✓ 已写入 ${FILE}（Portainer 需挂载 /home/john-han/.secrets:/run/john-secrets:ro）"
