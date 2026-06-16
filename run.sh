#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PID="$RUN_DIR/backend.pid"
FRONTEND_PID="$RUN_DIR/frontend.pid"

CMD="${1:-start}"

case "$CMD" in
  start)
    mkdir -p "$RUN_DIR" "$BACKEND_DIR/data"

    if [[ ! -f "$BACKEND_DIR/.env" ]]; then
      cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    fi

    if command -v tailscale >/dev/null 2>&1 && [[ -f "$BACKEND_DIR/.env" ]]; then
      ts_ip=$(tailscale ip -4 john-server 2>/dev/null | head -1 || true)
      if [[ -n "$ts_ip" ]] && grep -q 'S3_ENDPOINT_URL=http://john-server:19000' "$BACKEND_DIR/.env"; then
        sed -i.bak "s|S3_ENDPOINT_URL=http://john-server:19000|S3_ENDPOINT_URL=http://${ts_ip}:19000|" "$BACKEND_DIR/.env"
        rm -f "$BACKEND_DIR/.env.bak"
      fi
    fi

    if [[ -f "$BACKEND_DIR/.env" ]]; then
      db_line=$(grep -E '^DATABASE_URL=' "$BACKEND_DIR/.env" | head -1 || true)
      bucket_line=$(grep -E '^S3_BUCKET=' "$BACKEND_DIR/.env" | head -1 || true)
      echo "[start] ${db_line:-DATABASE_URL=（未配置）}"
      echo "[start] ${bucket_line:-S3_BUCKET=（未配置）}"
    fi
    if [[ ! -f "$FRONTEND_DIR/.env" ]]; then
      cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
    fi

    if [[ ! -d "$BACKEND_DIR/.venv" ]]; then
      echo "[start] 创建 Python 虚拟环境..."
      python3 -m venv "$BACKEND_DIR/.venv"
    fi
    # shellcheck disable=SC1091
    source "$BACKEND_DIR/.venv/bin/activate"
    pip install -q -U pip
    pip install -q -r "$BACKEND_DIR/requirements.txt"

    if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
      echo "[start] 安装前端依赖..."
      (cd "$FRONTEND_DIR" && npm install)
    fi

    if [[ -f "$BACKEND_PID" ]] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
      echo "[start] 后端已在运行 (pid $(cat "$BACKEND_PID"))"
    else
      echo "[start] 启动后端 http://localhost:${BACKEND_PORT}"
      (
        cd "$BACKEND_DIR"
        # shellcheck disable=SC1091
        source .venv/bin/activate
        nohup uvicorn app.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" \
          >"$RUN_DIR/backend.log" 2>&1 &
        echo $! >"$BACKEND_PID"
      )
    fi

    if [[ -f "$FRONTEND_PID" ]] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
      echo "[start] 前端已在运行 (pid $(cat "$FRONTEND_PID"))"
    else
      echo "[start] 启动前端 http://localhost:${FRONTEND_PORT}"
      (
        cd "$FRONTEND_DIR"
        nohup npm run dev -- --port "$FRONTEND_PORT" \
          >"$RUN_DIR/frontend.log" 2>&1 &
        echo $! >"$FRONTEND_PID"
      )
    fi

    echo "[start] 完成"
    echo "  前端: http://localhost:${FRONTEND_PORT}"
    echo "  后端: http://localhost:${BACKEND_PORT}"
    echo "  日志: $RUN_DIR/backend.log  $RUN_DIR/frontend.log"
    ;;

  stop)
     echo "[stop] 停止服务..."
    if [[ -f "$BACKEND_PID" ]]; then
      kill "$(cat "$BACKEND_PID")" 2>/dev/null || true
      rm -f "$BACKEND_PID"
    fi
    if [[ -f "$FRONTEND_PID" ]]; then
      kill "$(cat "$FRONTEND_PID")" 2>/dev/null || true
      rm -f "$FRONTEND_PID"
    fi

    # 清理仍占用端口的进程（如上次异常退出遗留）
    for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
      pids=$(lsof -ti tcp:"$port" 2>/dev/null || true)
      if [[ -n "$pids" ]]; then
        kill $pids 2>/dev/null || true
      fi
    done

    echo "[stop] 服务已停止"
    ;;

  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;

  *)
    echo "用法: $0 {start|stop|restart}"
    exit 1
    ;;
esac
