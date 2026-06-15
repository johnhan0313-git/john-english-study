# Portainer 生产部署（GitHub）

应用 Stack 与 PostgreSQL、MinIO 均为 Portainer 独立 Stack，通过 **共享 Docker 网络**互联。

仓库：<https://github.com/johnhan0313-git/john-english-study>

## 1. 预创建资源（john-server，已完成可跳过）

### PostgreSQL

```sql
CREATE USER "english-study" WITH PASSWORD 'english-study-123';
CREATE DATABASE "english-study" OWNER "english-study";
GRANT ALL PRIVILEGES ON DATABASE "english-study" TO "english-study";
```

在 `postgres` 容器内执行：`docker exec -it postgres psql -U appuser -d appdb`

### MinIO bucket

```bash
docker run --rm --network john-minio_default --entrypoint /bin/sh minio/mc:latest \
  -c "mc alias set myminio http://john-minio:9000 minioadmin minioadmin && mc mb --ignore-existing myminio/english-study-bucket"
```

## 2. Portainer 从 GitHub 部署

**不要**只粘贴 compose 内容；需让 Portainer **clone 整个仓库**后再 build。

1. 打开 Portainer → **Stacks** → **Add stack**
2. 名称：`john-english-study`（随意）
3. 选 **Git repository**（或 Repository）
4. 填写：
   - **Repository URL**：`https://github.com/johnhan0313-git/john-english-study.git`
   - **Repository reference**：`refs/heads/main`（或你的默认分支）
   - **Compose path**：`docker-compose.prod.yml`
   - 私有仓库：在 Portainer **Settings → Git credentials** 添加 GitHub PAT
5. **Environment variables**（可选，覆盖 compose 里的默认值）：
   - `JWT_SECRET` — 生产随机字符串
   - `AI_LLM_API_KEY` 等 AI 配置（backend 环境变量需在 compose 中扩展或通过 Portainer env 注入）
6. 若 Portainer 支持编辑 compose，确认 frontend build arg：

   ```yaml
   frontend:
     build:
       context: ./frontend
       args:
         NEXT_PUBLIC_API_URL: http://john-server:8000/api   # 改成浏览器实际访问后端的地址
   ```

7. 点击 **Deploy the stack**

Portainer 会在 john-server 上：clone 代码 → `docker build` backend/frontend → 启动容器。

### 更新部署

代码 push 到 GitHub 后，在 Portainer Stack 页面点 **Pull and redeploy**（或 Rebuild），会重新 clone 并 build。

改 `NEXT_PUBLIC_API_URL` 后必须 **重新 build frontend**，不能只 restart。

## 3. 连接地址（容器内互联）

| 变量 | 值（共享 Docker 网络） |
|------|------------------------|
| `DATABASE_URL` | `postgresql+psycopg://english-study:english-study-123@postgres:5432/english-study` |
| `S3_ENDPOINT_URL` | `http://john-minio:9000` |
| `S3_BUCKET` | `english-study-bucket` |

`john-postgres_default`、`john-minio_default` 须已存在（PG/MinIO Stack 创建时会自动生成）。

## 4. 浏览器访问地址示例

| 访问方式 | 前端 | `NEXT_PUBLIC_API_URL` | `CORS_ORIGINS` |
|----------|------|------------------------|----------------|
| 本机浏览器 | `http://localhost:3000` | `http://localhost:8000/api` | `http://localhost:3000` |
| 局域网/域名 | `http://john-server:3000` | `http://john-server:8000/api` | `http://john-server:3000` |

MinIO Console **19101** 仅供管理；S3 API 为 **9000**（容器内）/ **19000**（宿主机）。

## 5. 验证

- Stack 日志：backend 出现 `alembic upgrade head` 成功
- http://john-server:8000/docs
- http://john-server:3000 登录、头像、音频

## 6. 多实例注意

- 多 backend 副本：`ENABLE_SCHEDULER=false`，cron 调用 `python -m app.cli daily-scenarios`
- 验证码/OTP 在进程内存，多副本需后续 Redis
