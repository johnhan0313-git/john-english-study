# Portainer 生产部署（GitHub）

仓库：<https://github.com/johnhan0313-git/john-english-study>

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
