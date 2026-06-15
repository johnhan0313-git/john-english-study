# Backend data directory

运行时数据目录，默认 `backend/data`（容器内 `/app/data`）。

## 文件说明

| 文件 | 必需 | 说明 |
|------|------|------|
| `dict_lookup.json` | 推荐 | 约 1.2 万词中文释义；**首次启动会自动从 GitHub 下载生成** |
| `word_groups.json` | 可选 | 主题词分组 |
| `pets_words.json` | 可选 | PETS 等级词库扩展 |
| `dict_lookup_overrides.json` | 可选 | 释义覆盖 |

## 生产部署（Portainer）

`docker-compose.prod.yml` 已挂载 Docker volume：

```yaml
volumes:
  - english_study_data:/app/data
environment:
  DATA_DIR: /app/data
```

- 首次启动：容器内自动下载生成 `dict_lookup.json`（约 1–2 分钟，需能访问 GitHub）
- 之后重建容器：volume 保留，无需重复下载

## 本地手动生成

```bash
cd backend
python -m app.cli ensure-data
# 或
python scripts/build_dict_lookup.py
```

## 宿主机目录挂载（可选）

若希望数据在宿主机固定路径，可将 compose 中 volume 改为：

```yaml
volumes:
  - /opt/john-english-study/data:/app/data
```

事先创建目录：`mkdir -p /opt/john-english-study/data`
