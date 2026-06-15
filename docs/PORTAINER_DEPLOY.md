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

## 数据目录

`docker-compose.prod.yml` 已挂载 volume **`english_study_data` → `/app/data`**。

- 首次启动：`docker-entrypoint.sh` 会执行 `python -m app.cli ensure-data`，自动下载生成 `dict_lookup.json`（需访问 GitHub，约 1–2 分钟）
- 重建容器：volume 保留，无需重复下载
- 详见 [backend/data/README.md](../backend/data/README.md)

## Portainer 部署步骤

1. Stacks → Add stack → **Git repository**
2. URL：`https://github.com/johnhan0313-git/john-english-study.git`
3. Compose path：`docker-compose.prod.yml`
4. 覆盖 `JWT_SECRET`、`CORS_ORIGINS`、frontend `NEXT_PUBLIC_API_URL`、**SMTP_***（见下）
5. Deploy

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
| `DATABASE_URL` | `postgresql+psycopg://english-study:english-study-123@postgres:5432/english-study` |
| `S3_ENDPOINT_URL` | `http://john-minio:9000` |
| `DATA_DIR` | `/app/data` |

## Cloudflare Tunnel（es.cool-app.me）

`~/.cloudflared/config.yml` 示例：

```yaml
ingress:
  - hostname: es.cool-app.me
    path: ^/api(/.*)?$
    service: http://localhost:8000
  - hostname: es.cool-app.me
    service: http://localhost:3000
  - service: http_status:404
```

**注意**：`path` 是 **Go 正则**，不是 glob。`/api*` 会误匹配 `/_next/static/chunks/app/*.js`（路径里的 `/app` 满足 `/ap` + `i*`=0），导致静态资源被转发到 FastAPI 并返回 `{"detail":"Not Found"}`。

修改后重启 tunnel 并验证：

```bash
cloudflared tunnel --config ~/.cloudflared/config.yml ingress rule \
  "https://es.cool-app.me/_next/static/chunks/app/page.js"   # 应匹配 frontend:3000

sudo systemctl restart cloudflared
```

在 Cloudflare 控制台 **Caching → Purge Everything** 清掉之前缓存的 404。
