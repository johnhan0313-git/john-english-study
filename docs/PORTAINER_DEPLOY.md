# Portainer 生产部署

应用 Stack 与 PostgreSQL、MinIO 均为 Portainer 独立 Stack，通过 **共享 Docker 网络**互联。

## 1. 预创建资源（john-server 一次性）

### PostgreSQL

```sql
CREATE USER "english-study" WITH PASSWORD 'english-study-123';
CREATE DATABASE "english-study" OWNER "english-study";
GRANT ALL PRIVILEGES ON DATABASE "english-study" TO "english-study";
```

在 `postgres` 容器内执行：`docker exec -it postgres psql -U postgres`

### MinIO bucket

```bash
docker run --rm --network john-minio_default --entrypoint /bin/sh minio/mc:latest \
  -c "mc alias set myminio http://john-minio:9000 minioadmin minioadmin && mc mb --ignore-existing myminio/english-study-bucket"
```

## 2. 部署应用 Stack

Portainer → Stacks → Add Stack → 使用仓库内 [docker-compose.prod.yml](../docker-compose.prod.yml)。

部署前在 Portainer UI 覆盖：

- `JWT_SECRET` — 生产随机密钥
- `AI_LLM_API_KEY` 等 AI 配置
- `CORS_ORIGINS` — 实际前端域名
- `NEXT_PUBLIC_API_URL`（frontend build arg）— 浏览器可访问的后端 API 地址

## 3. 连接地址说明

| 场景 | DATABASE_URL host | S3_ENDPOINT_URL |
|------|-------------------|-----------------|
| Portainer 容器，共享网络（推荐） | `postgres:5432/english-study` | `http://john-minio:9000` |
| 容器走宿主机端口（备选） | `host.docker.internal:5432` | `http://host.docker.internal:19000` |
| 宿主机直跑 backend | `localhost:5432` | `http://localhost:19000` |

MinIO Console 端口 **19101** 仅供浏览器管理；S3 API 为容器内 **9000** / 宿主机 **19000**。

## 4. 验证

- backend 日志：`alembic upgrade head` 成功
- http://localhost:8000/docs
- 前端登录、头像上传、场景/对话音频播放

## 5. 多实例注意

- 多 backend 副本时设 `ENABLE_SCHEDULER=false`，用 cron 调用 `python -m app.cli daily-scenarios`
- 验证码/OTP 仍存进程内存，多副本需后续引入 Redis
