# 本地测试环境（PostgreSQL + MinIO）

## 推荐：完全自包含测试环境

不依赖 Tailscale 或 john-server，Docker 会临时启动 PostgreSQL、MinIO 和测试容器，结束后自动清理：

```bash
./scripts/test-env.sh
# 只跑指定文件
./scripts/test-env.sh tests/test_ai_provider.py
```

对应文件为 `docker-compose.test.yml` 和 `.env.test.example`。测试资源只存在于临时容器，不会接触生产数据库或 bucket。

## 远程 1:1 测试环境

本地 `./run.sh start` 启动前后端，数据库与对象存储连接 john-server 上与生产 **1:1** 的测试资源（`-test` 后缀），通过 **Tailscale** 访问。

生产部署见 [PORTAINER_DEPLOY.md](PORTAINER_DEPLOY.md)。

## 架构

```
本地 Mac/PC                    john-server (Tailscale)
┌─────────────────┐           ┌──────────────────────────┐
│ run.sh          │           │ john-postgresql :5432    │
│  frontend :3000 │           │   └─ english-study-test  │
│  backend  :8000 │──Tailscale│ john-minio :19000        │
└─────────────────┘           │   └─ english-study-      │
                              │      bucket-test         │
                              └──────────────────────────┘
```

| 资源 | 生产 | 本地测试 |
|------|------|----------|
| PostgreSQL 库 | `english-study` | `english-study-test` |
| MinIO bucket | `english-study-bucket` | `english-study-bucket-test` |
| 媒体文件 | MinIO | MinIO（同上 bucket） |
| 词库释义 | PG `dictionary_entries` | 同上（测试库） |

## 前置条件

1. 本机已加入 Tailscale，能 ping / ssh `john-server`
2. john-server 上 PG **5432**、MinIO **19000**（宿主机映射，容器内为 9000）对 Tailscale 可达

验证：

```bash
nc -zv john-server 5432
nc -zv john-server 19000
```

**MinIO S3 API 502**：若 `S3_ENDPOINT_URL` 使用 hostname 报 502，改用 Tailscale IP（`tailscale ip -4 john-server`）。`run.sh` 与 pytest 会在检测到 `tailscale` CLI 时自动将 `john-server` 解析为 Tailscale IP。

```env
S3_ENDPOINT_URL=http://100.x.x.x:19000
```

## john-server 一次性初始化

测试库（若尚未创建）：

```bash
ssh john-server 'docker exec john-postgresql psql -U appuser -d appdb -c \
  "CREATE DATABASE \"english-study-test\" OWNER \"english-study\";"'
```

MinIO bucket 会在 backend 首次连接时自动创建（`english-study-bucket-test`）。

## 本地启动

```bash
cp backend/.env.example backend/.env   # 首次；按需改 john-server 主机名
./run.sh start
```

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- 日志：`.run/backend.log`、`.run/frontend.log`

`run.sh` 启动时会打印 `DATABASE_URL` 与 `S3_BUCKET`，请确认指向 `-test` 资源。

首次启动后若词库为空，可手动灌库：

```bash
cd backend && source .venv/bin/activate
python -m app.cli seed-dictionary
python -m app.cli seed
```

## 跑测试

pytest 与 run.sh **共用** `backend/.env`（不存在时回退 `.env.example`），并强制校验：

- 数据库必须是 `english-study-test`
- S3 bucket 必须是 `english-study-bucket-test`

```bash
cd backend
source .venv/bin/activate
pytest
```

每个用例前会清空 MinIO 测试 bucket，并重置用户/场景等业务表；词库等 seed 表在 session 内只灌一次。

## 环境变量要点

见 [backend/.env.example](../backend/.env.example)：

| 变量 | 本地测试值 |
|------|-----------|
| `DATABASE_URL` | `postgresql+psycopg://english-study:...@john-server:5432/english-study-test` |
| `USE_MIGRATIONS` | `true` |
| `STORAGE_BACKEND` | `s3` |
| `S3_ENDPOINT_URL` | `http://john-server:19000` |
| `S3_BUCKET` | `english-study-bucket-test` |
| `ENABLE_SCHEDULER` | `false` |
| `AUTH_EXPOSE_CODES` | `true` |
| `SKIP_STARTUP_SEED` | `true`（跳过词库同步；音标/语法仍会在启动时自动灌库） |

## 与生产隔离

- **禁止** 本地 `.env` 指向 `english-study` 库或 `english-study-bucket`
- pytest 启动时会断言，误配会立即失败
- 生产 Stack 仍用 `docker-compose.prod.yml`，与本地测试无关
