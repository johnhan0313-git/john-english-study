#!/usr/bin/env bash
# 修复 Cursor 本机升级后 Remote SSH 卡在「Install in progress / 下载超时 / 锁冲突」的问题。
#
# 典型症状：
#   - SSH 正常，但 Cursor Remote SSH 连不上
#   - 日志出现 Install in progress / Could not acquire lock / Download failed
#
# 用法：
#   ./scripts/fix-cursor-remote-ssh.sh john-server
#   ./scripts/fix-cursor-remote-ssh.sh --host john-server
#   ./scripts/fix-cursor-remote-ssh.sh --clean-only john-server
#   ./scripts/fix-cursor-remote-ssh.sh --no-proxy john-server
#
set -euo pipefail

HOST=""
MODE="install"   # install | clean-only
FORCE_KILL_SERVER=0
USE_PROXY=1
REMOTE_PROXY=""   # 空 = 自动检测远程机代理
SSH_OPTS=()

usage() {
  cat <<'EOF'
用法: fix-cursor-remote-ssh.sh [选项] [SSH_HOST]

修复 Cursor Remote SSH 因本机升级导致远程 Server 安装卡住的问题。
默认在远程机器下载 Cursor Server，并走远程机自己的代理（如 mihomo/clash）。

参数:
  SSH_HOST              ~/.ssh/config 中的 Host 名，默认 john-server

选项:
  -h, --host HOST       指定 SSH Host（与 positional 二选一）
  --clean-only          仅清理远程锁/卡死进程/残缺下载，不下载安装
  --no-proxy            远程直连下载，不走代理
  --proxy URL           指定远程机代理地址，默认自动检测（如 http://127.0.0.1:7890）
  --force               清理时同时停止正在运行的旧 cursor-server 进程
  --ssh-opt OPT         额外传给 ssh 的参数，可重复
  --help                显示帮助

示例:
  ./scripts/fix-cursor-remote-ssh.sh john-server
  ./scripts/fix-cursor-remote-ssh.sh --clean-only john-server
  ./scripts/fix-cursor-remote-ssh.sh --proxy http://127.0.0.1:7890 --host john-server-out
EOF
}

log()  { printf '\033[1;34m[fix-cursor]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[fix-cursor]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[fix-cursor]\033[0m %s\n' "$*" >&2; exit 1; }

run_ssh() {
  if ((${#SSH_OPTS[@]} > 0)); then
    ssh "${SSH_OPTS[@]}" "$@"
  else
    ssh "$@"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--host)
      [[ $# -ge 2 ]] || die "缺少 --host 参数"
      HOST="$2"
      shift 2
      ;;
    --clean-only)
      MODE="clean-only"
      shift
      ;;
    --no-proxy)
      USE_PROXY=0
      shift
      ;;
    --proxy)
      [[ $# -ge 2 ]] || die "缺少 --proxy 参数"
      REMOTE_PROXY="$2"
      USE_PROXY=1
      shift 2
      ;;
    --force)
      FORCE_KILL_SERVER=1
      shift
      ;;
    --ssh-opt)
      [[ $# -ge 2 ]] || die "缺少 --ssh-opt 参数"
      SSH_OPTS+=("$2")
      shift 2
      ;;
    --help|-?)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    -*)
      die "未知选项: $1（使用 --help 查看帮助）"
      ;;
    *)
      [[ -z "$HOST" ]] || die "重复指定 Host: $1"
      HOST="$1"
      shift
      ;;
  esac
done

HOST="${HOST:-john-server}"

find_product_json() {
  local candidate
  for candidate in \
    "/Applications/Cursor.app/Contents/Resources/app/product.json" \
    "$HOME/Applications/Cursor.app/Contents/Resources/app/product.json" \
    "/usr/share/cursor/resources/app/product.json" \
    "$HOME/.local/share/cursor/resources/app/product.json"
  do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

read_cursor_metadata() {
  local product_json
  product_json="$(find_product_json)" || die "找不到本机 Cursor product.json，请确认已安装 Cursor"

  if ! command -v python3 >/dev/null 2>&1; then
    die "需要 python3 来读取 Cursor 版本信息"
  fi

  python3 - "$product_json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as f:
    data = json.load(f)

commit = data.get("commit") or data.get("nightlyCommit")
real_commit = data.get("realCommit") or commit
quality = data.get("quality", "stable")
version = data.get("version", "unknown")

line = "nightly" if quality == "insider" else "production"
if not commit or not real_commit:
    raise SystemExit("product.json 缺少 commit / realCommit")

print(f"CURSOR_VERSION={version}")
print(f"CURSOR_COMMIT={commit}")
print(f"CURSOR_REAL_COMMIT={real_commit}")
print(f"CURSOR_LINE={line}")
print(f"CURSOR_PRODUCT_JSON={path}")
PY
}

remote_arch() {
  run_ssh "$HOST" 'case "$(uname -m)" in
    x86_64|amd64) echo x64 ;;
    aarch64|arm64) echo arm64 ;;
    *) echo "unsupported:$(uname -m)" >&2; exit 1 ;;
  esac'
}

detect_remote_proxy() {
  run_ssh "$HOST" bash -s <<'REMOTE'
set -euo pipefail

read_shell_proxy() {
  local rc host port
  for rc in "${HOME}/.zshrc" "${HOME}/.bashrc" "${HOME}/.profile"; do
    [[ -f "${rc}" ]] || continue
    host="$(grep -E '^_proxy_host=' "${rc}" | head -1 | sed -E 's/^[^=]+="?([^"]+)"?.*/\1/')"
    port="$(grep -E '^_proxy_http_port=' "${rc}" | head -1 | sed -E 's/^[^=]+="?([^"]+)"?.*/\1/')"
    if [[ -n "${host}" && -n "${port}" ]]; then
      printf 'http://%s:%s\n' "${host}" "${port}"
      return 0
    fi
  done
  return 1
}

port_listening() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -tln | grep -qE ":${port}([^0-9]|$)"
    return
  fi
  if command -v lsof >/dev/null 2>&1; then
    lsof -i ":${port}" -sTCP:LISTEN >/dev/null 2>&1
    return
  fi
  return 1
}

if proxy_url="$(read_shell_proxy 2>/dev/null)"; then
  port="${proxy_url##*:}"
  if port_listening "${port}"; then
    printf '%s\n' "${proxy_url}"
    exit 0
  fi
fi

for port in 7890 7897 10809 1080 8080 3128; do
  if port_listening "${port}"; then
    printf 'http://127.0.0.1:%s\n' "${port}"
    exit 0
  fi
done

exit 1
REMOTE
}

resolve_remote_proxy() {
  if [[ "${USE_PROXY}" != "1" ]]; then
    printf '\n'
    return 0
  fi

  if [[ -n "${REMOTE_PROXY}" ]]; then
    printf '%s\n' "${REMOTE_PROXY}"
    return 0
  fi

  if proxy_url="$(detect_remote_proxy)"; then
    printf '%s\n' "${proxy_url}"
    return 0
  fi

  warn "未检测到远程代理，将 IPv4 直连下载"
  printf '\n'
}

remote_cleanup() {
  local force="$1"
  log "清理远程卡死状态: $HOST"
  run_ssh "$HOST" "FORCE_KILL_SERVER=$force" bash -s <<'REMOTE'
set -euo pipefail

SERVER_ROOT="${HOME}/.cursor-server"
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

echo "  runtime dir: ${RUNTIME_DIR}"

if [[ "${FORCE_KILL_SERVER}" == "1" ]]; then
  echo "  停止旧 cursor-server 进程..."
  pkill -f "${SERVER_ROOT}/bin/.*/out/server-main.js" 2>/dev/null || true
  pkill -f "${SERVER_ROOT}/bin/.*/bin/cursor-server" 2>/dev/null || true
  sleep 1
fi

echo "  停止卡住的安装/下载进程..."
pkill -f 'downloads\.cursor\.com/.*/cursor-reh-' 2>/dev/null || true
pkill -f 'cursor\.blob\.core\.windows\.net/.*/vscode-reh-' 2>/dev/null || true
pkill -f 'cursor-server-.*\.tar\.gz' 2>/dev/null || true

while read -r pid cmd; do
  [[ -z "${pid}" ]] && continue
  case "${cmd}" in
    *downloads.cursor.com*|*cursor-reh*|*cursor-server-*.tar.gz*)
      kill "${pid}" 2>/dev/null || true
      ;;
  esac
done < <(ps -eo pid=,args= | grep -E 'wget|curl' | grep -v grep || true)

echo "  删除安装锁..."
rm -f "${RUNTIME_DIR}"/cursor-remote-lock.* 2>/dev/null || true

echo "  删除残缺 tar 包..."
find "${SERVER_ROOT}/bin" -type f \( -name 'cursor-server-*.tar.gz' -o -name 'cursor-reh-*.tar.gz' \) -delete 2>/dev/null || true

echo "  清理完成"
REMOTE
}

server_installed() {
  local commit="$1"
  run_ssh "$HOST" "test -x \"\${HOME}/.cursor-server/bin/linux-x64/${commit}/node\""
}

extract_remote() {
  local commit="$1"
  local tarball_name="$2"
  run_ssh "$HOST" "COMMIT=${commit} TARBALL=${tarball_name}" bash -s <<'REMOTE'
set -euo pipefail

INSTALL_DIR="${HOME}/.cursor-server/bin/linux-x64/${COMMIT}"
TARBALL_PATH="${INSTALL_DIR}/${TARBALL}"

[[ -f "${TARBALL_PATH}" ]] || { echo "tar 包不存在: ${TARBALL_PATH}" >&2; exit 1; }

mkdir -p "${INSTALL_DIR}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "  解压 ${TARBALL} ..."
tar -xzf "${TARBALL_PATH}" -C "${TMP_DIR}"

SRC="${TMP_DIR}"
if [[ -d "${TMP_DIR}/vscode-reh-linux-x64" ]]; then
  SRC="${TMP_DIR}/vscode-reh-linux-x64"
elif [[ -d "${TMP_DIR}/cursor-reh-linux-x64" ]]; then
  SRC="${TMP_DIR}/cursor-reh-linux-x64"
else
  subdirs=( "${TMP_DIR}"/* )
  if [[ ${#subdirs[@]} -eq 1 && -d "${subdirs[0]}" ]]; then
    SRC="${subdirs[0]}"
  fi
fi

shopt -s dotglob
cp -a "${SRC}/." "${INSTALL_DIR}/"
rm -f "${TARBALL_PATH}"

if [[ ! -x "${INSTALL_DIR}/node" ]]; then
  echo "解压后未找到 node 可执行文件: ${INSTALL_DIR}/node" >&2
  exit 1
fi

echo "  安装目录: ${INSTALL_DIR}"
REMOTE
}

install_via_remote_download() {
  local line="$1"
  local real_commit="$2"
  local commit="$3"
  local arch="$4"
  local remote_proxy_url="$5"

  local url="https://downloads.cursor.com/${line}/${real_commit}/linux/${arch}/cursor-reh-linux-${arch}.tar.gz"
  local tarball="cursor-reh-linux-${arch}.tar.gz"

  log "远程下载 Cursor Server"
  log "  URL: ${url}"
  if [[ -n "${remote_proxy_url}" ]]; then
    log "  代理: ${remote_proxy_url}（远程机本地代理）"
  else
    log "  代理: 无（IPv4 直连）"
  fi

  run_ssh "$HOST" "URL=${url} COMMIT=${commit} TARBALL=${tarball} REMOTE_PROXY=${remote_proxy_url}" bash -s <<'REMOTE'
set -euo pipefail

INSTALL_DIR="${HOME}/.cursor-server/bin/linux-x64/${COMMIT}"
TARBALL_PATH="${INSTALL_DIR}/${TARBALL}"
mkdir -p "${INSTALL_DIR}"

if [[ -f "${TARBALL_PATH}" ]]; then
  rm -f "${TARBALL_PATH}"
fi

CURL_ARGS=(
  -fL
  -4
  --retry 20
  --retry-all-errors
  --retry-delay 5
  --connect-timeout 30
  --continue-at -
  -o "${TARBALL_PATH}"
)

if [[ -n "${REMOTE_PROXY}" ]]; then
  export http_proxy="${REMOTE_PROXY}"
  export https_proxy="${REMOTE_PROXY}"
  export HTTP_PROXY="${REMOTE_PROXY}"
  export HTTPS_PROXY="${REMOTE_PROXY}"
  CURL_ARGS+=( -x "${REMOTE_PROXY}" )
fi

echo "  开始下载..."
curl "${CURL_ARGS[@]}" "${URL}"

HEAD_ARGS=( -fsSL -4 -I "${URL}" )
if [[ -n "${REMOTE_PROXY}" ]]; then
  HEAD_ARGS+=( -x "${REMOTE_PROXY}" )
fi
EXPECTED="$(curl "${HEAD_ARGS[@]}" | awk 'tolower($1)=="content-length:" {print $2}' | tr -d '\r')"
ACTUAL="$(wc -c < "${TARBALL_PATH}" | tr -d ' ')"
if [[ -n "${EXPECTED}" && "${ACTUAL}" != "${EXPECTED}" ]]; then
  echo "下载大小不匹配: ${ACTUAL}/${EXPECTED} bytes" >&2
  exit 1
fi

echo "  下载完成: ${ACTUAL} bytes"
REMOTE

  extract_remote "${commit}" "${tarball}"
}

main() {
  log "目标主机: ${HOST}"

  if ! run_ssh -o BatchMode=yes -o ConnectTimeout=10 "$HOST" 'echo ok' >/dev/null 2>&1; then
    die "无法 SSH 连接到 ${HOST}，请先确认 ssh ${HOST} 可用"
  fi

  eval "$(read_cursor_metadata)"
  log "本机 Cursor ${CURSOR_VERSION} (${CURSOR_PRODUCT_JSON})"
  log "  commit=${CURSOR_COMMIT}"
  log "  realCommit=${CURSOR_REAL_COMMIT}"

  ARCH="$(remote_arch)"
  log "远程架构: linux/${ARCH}"

  remote_cleanup "${FORCE_KILL_SERVER}"

  if [[ "${MODE}" == "clean-only" ]]; then
    log "仅清理模式完成。请在 Cursor 中重新连接 ${HOST}。"
    exit 0
  fi

  if server_installed "${CURSOR_COMMIT}"; then
    log "远程已存在匹配版本的 Cursor Server，无需重新安装。"
    log "请在 Cursor 中重新连接 ${HOST}。"
    exit 0
  fi

  REMOTE_PROXY_URL="$(resolve_remote_proxy)"

  install_via_remote_download \
    "${CURSOR_LINE}" \
    "${CURSOR_REAL_COMMIT}" \
    "${CURSOR_COMMIT}" \
    "${ARCH}" \
    "${REMOTE_PROXY_URL}"

  if ! server_installed "${CURSOR_COMMIT}"; then
    die "安装校验失败：远程 node 不存在"
  fi

  log "修复完成。"
  cat <<EOF

下一步：
  1. 打开 Cursor
  2. Command Palette -> Remote-SSH: Connect to Host -> ${HOST}
  3. 若仍失败，查看 Output -> Remote - SSH 日志

提示：
  - 默认在远程下载，并自动使用远程机本地代理（如 mihomo :7890）
  - 指定代理: $0 --proxy http://127.0.0.1:7890 ${HOST}
  - 不走代理: $0 --no-proxy ${HOST}
  - 仅清锁: $0 --clean-only ${HOST}
EOF
}

main
