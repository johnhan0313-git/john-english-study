# Portainer 生产部署（GitHub）

仓库：<https://github.com/johnhan0313-git/john-english-study>

## 部署方式选择

| 方式 | 适用 | 稳定性 |
|------|------|--------|
| **SSH + deploy 脚本（推荐）** | 日常发版、改环境变量 | 高，不依赖服务器访问 GitHub |
| Portainer Git Stack | 偶尔 Pull and redeploy | **低**，john-server 到 GitHub 经常超时/TLS 失败 |

### 推荐：SSH 部署脚本

john-server 访问 GitHub **极不稳定**（`curl github.com` 经常 10s 超时，`git clone` TLS 中断）。Portainer Git Stack 每次更新都要重新 clone，失败时会报：

- `dial tcp 20.205.243.166:443: i/o timeout`
- `Could not get the contents of the file 'docker-compose.prod.yml'`

**稳定做法**：在你本机 push 代码后，用 rsync 同步到服务器再 build：

```bash
# 1. 在 john-server 首次创建密钥文件（不要提交 git）
ssh john-server 'mkdir -p ~/apps/john-english-study'
scp .env.prod.example john-server:~/apps/john-english-study/.env.prod
# 编辑 .env.prod 填入 JWT_SECRET、SMTP_* 等

# 2. 本机执行部署
./scripts/deploy-john-server.sh
```

仅改环境变量时，直接改服务器上的 `~/.env.prod` 或 `~/apps/john-english-study/.env.prod`，再跑一遍脚本即可，**无需 Portainer Pull**。

### Portainer Git Stack（备选）

网络通畅时可用；若 Pull 失败但容器仍在跑，**不要反复点 Pull**，改用上面的 SSH 脚本。

#### 让 Portainer 走 mihomo 代理

john-server 上 mihomo 监听 `7890`（HTTP）、`7891`（SOCKS）。Portainer 在容器里 clone GitHub，需配置代理环境变量，并通过 `host.docker.internal` 访问宿主机 mihomo：

```yaml
# ~/portainer/portainer-compose.yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
environment:
  HTTP_PROXY: http://host.docker.internal:7890
  HTTPS_PROXY: http://host.docker.internal:7890
  NO_PROXY: localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8,172.16.0.0/12
```

修改后 `docker compose up -d` 重启 Portainer。**mihomo 必须保持运行**，否则 Pull 仍会失败。内网服务（postgres、minio 等）在 `NO_PROXY` 里，不会误走代理。

### Docker 构建时 pip 很慢

john-server 直连官方 PyPI 易超时。默认使用**清华镜像直连**（无需 mihomo），一般 1–3 分钟装完。

**镜像 OR 代理，二选一**，不要同时开：

- 默认：`PIP_INDEX_URL` 清华源，`PIP_HTTP_PROXY` 留空
- 备选（镜像不可用）：清空 `PIP_INDEX_URL`，改设 `PIP_HTTP_PROXY` / `PIP_HTTPS_PROXY` 走 mihomo

重新部署：

```bash
./scripts/deploy-john-server.sh
```

可在 `.env.prod` 覆盖：

```bash
# 推荐（默认）
PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# 或镜像挂了时
# PIP_INDEX_URL=
# PIP_HTTP_PROXY=http://host.docker.internal:7890
# PIP_HTTPS_PROXY=http://host.docker.internal:7890
```

临时手动构建：

```bash
cd ~/apps/john-english-study
docker compose --env-file .env.prod -f docker-compose.prod.yml build \
  --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple backend
```

## 词库初始化

容器启动时 `docker-entrypoint.sh` 会依次执行：

1. `alembic upgrade head`
2. `python -m app.cli seed-dictionary`（`dictionary_entries` 表为空时从 GitHub 拉取，约 1–2 分钟）

重建容器后数据仍在 PostgreSQL，**无需重复下载**。

已有生产库首次升级后，可手动执行：

```bash
docker exec <backend-container> python -m app.cli seed-dictionary
docker exec <backend-container> python -m app.cli seed
```

## GitHub Packages token（构建 frontend）

与 john-readhub 相同：服务器一次执行 `scripts/setup-server-secrets.sh`，Portainer 挂载 `/home/john-han/.secrets:/run/john-secrets:ro`（`deploy/portainer-compose.example.yaml`）。**勿**在 Stack 环境变量填 token。

## Portainer 部署步骤

1. Stacks → Add stack → **Git repository**
2. URL：`https://github.com/johnhan0313-git/john-english-study.git`
3. Compose path：`docker-compose.prod.yml`
4. 在 Stack Environment variables 填入 `.env.prod.example` 中的变量。`DATABASE_URL`、`S3_ACCESS_KEY`、`S3_SECRET_KEY`、`JWT_SECRET` 为强制项，缺失时 Compose 会拒绝部署。
5. Deploy

部署前可在本机使用相同环境文件检查：

```bash
./scripts/validate-deployment.sh .env.prod
```

部署成功后 Portainer 应显示 backend/frontend 均为 `healthy`。后端健康地址为 `/api/health`。

## 邮件验证码（SMTP）

生产容器**未配置 SMTP 时**，`/api/auth/email/send-code` 仍会返回成功，但**不会发邮件**（验证码只写后端日志，且 `dev_code` 为 null）。

在 Portainer Stack **Environment variables** 中添加（163 邮箱示例）：

| 变量 | 值 |
|------|-----|
| `SMTP_HOST` | `smtp.163.com` |
| `SMTP_PORT` | `465` |
| `SMTP_USER` | 你的发信邮箱 |
| `SMTP_PASSWORD` | 163 授权码（非登录密码） |
| `SMTP_FROM` | 与 `SMTP_USER` 相同 |
| `SMTP_USE_TLS` | `false` |
| `SMTP_USE_SSL` | `true` |

保存后 **Update the stack** 重启 backend。验证：

```bash
docker exec john-english-study-backend-1 python -c \
  "from app.config import get_settings; s=get_settings(); print(s.smtp_configured)"
# 应输出 True
```

## 连接地址（共享 Docker 网络）

| 变量 | 值 |
|------|-----|
| `DATABASE_URL` | `postgresql+psycopg://english-study:english-study-123@john-postgresql:5432/english-study` |
| `S3_ENDPOINT_URL` | `http://john-minio:9000` |

## Cloudflare Tunnel + nginx（se.cool-app.me）

流量路径：`se.cool-app.me` → cloudflared → nginx:1180 → frontend/backend 容器。

`~/.cloudflared/config.yml` 示例：

```yaml
ingress:
  - hostname: se.cool-app.me
    service: http://localhost:1180
  - hostname: "*.cool-app.me"
    service: http://localhost:1180
  - service: http_status:404
```

nginx 路由见 `~/mydocker/mntdata/nginx/nginx.conf`（`se.cool-app.me` 的 `/api/` → backend，其余 → frontend）。

修改 nginx 或 cloudflared 后：

```bash
docker exec john-nginx nginx -t && docker restart john-nginx
sudo systemctl restart cloudflared
```

Cloudflare DNS 需有 `se.cool-app.me` CNAME 指向 Tunnel。改域名后在 **Caching → Purge Everything** 清缓存。
