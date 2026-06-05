# PostgreSQL 迁移指南

MVP 使用 SQLite，扩展为多用户云部署时可迁移到 PostgreSQL。

## 1. 修改环境变量

```env
DATABASE_URL=postgresql://user:password@localhost:5432/john_english_study
```

## 2. 安装依赖

```bash
pip install psycopg2-binary
```

## 3. 初始化 Alembic（可选）

```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

当前 MVP 使用 `Base.metadata.create_all()` 自动建表，迁移时可切换为 Alembic 管理。

## 4. 数据迁移

从 SQLite 导出再导入 PostgreSQL：

```bash
# 导出词汇（示例）
sqlite3 backend/data/app.db .dump > dump.sql
# 或使用 Python 脚本逐表迁移
```

## 5. 注意事项

- SQLite 的 `check_same_thread=False` 在 PostgreSQL 下不需要
- 生产环境建议启用 JWT 认证（`/api/auth/register`, `/api/auth/login`）
- 媒体文件建议使用对象存储（S3/OSS）替代本地 `media_dir`
