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
4. 覆盖 `JWT_SECRET`、`CORS_ORIGINS`、frontend `NEXT_PUBLIC_API_URL`
5. Deploy

## 连接地址（共享 Docker 网络）

| 变量 | 值 |
|------|-----|
| `DATABASE_URL` | `postgresql+psycopg://english-study:english-study-123@postgres:5432/english-study` |
| `S3_ENDPOINT_URL` | `http://john-minio:9000` |
| `DATA_DIR` | `/app/data` |
