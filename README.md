# SceneEnglish — 成人英语场景学习平台

对标 CET-4/6 的成人英语学习网站，以场景化词汇学习为核心，兼顾听说读写，支持 AI 生成场景与练习题。

## 功能

- **词库**：CET-4/6 + PETS 公共英语等级考试词库，按主题分组浏览
- **场景学习**：AI 生成叙事/对话场景，高亮目标词汇
- **练习**：单选题、填空题，SRS 间隔重复
- **听力**：Edge TTS / OpenAI TTS 音频播放，多语速
- **口语**：录音跟读 + STT 评测
- **写作**：AI 批改（需配置 API Key）
- **每日场景**：自动推送复习/新词/挑战 3 个场景

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 20+（前端）
- **Tailscale** 连通 john-server（数据库与 MinIO 在远程，见 [docs/TEST_ENV.md](docs/TEST_ENV.md)）
- OpenAI 兼容 API Key（可选，未配置时使用 Mock 数据）

### 一键启动（推荐）

```bash
cp backend/.env.example backend/.env   # 首次
cp apps/web/.env.example apps/web/.env # 首次
./run.sh start
```

访问 http://localhost:3000

### 后端（手动）

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 backend/.env 填入 AI_LLM_API_KEY 等（默认已指向 john-server 测试 PG + MinIO）

uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd apps/web
npm install
cp .env.example .env
npm run dev
```

访问 http://localhost:3000

### Docker

```bash
cp backend/.env.example backend/.env
cp apps/web/.env.example apps/web/.env
docker compose up --build
```

`NEXT_PUBLIC_API_URL` 在 **构建期** 注入 Next.js，修改后需重新 build。示例：

```yaml
# docker-compose.yml
services:
  frontend:
    build:
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000/api
```

## 环境变量

- 后端：[backend/.env.example](backend/.env.example)
- 前端：[apps/web/.env.example](apps/web/.env.example)

后端关键配置：

| 变量 | 说明 |
|------|------|
| `AI_LLM_*` / `AI_STT_*` / `AI_TTS_*` | 按能力分别配置 API（可混用 Groq、DeepSeek、OpenAI 等） |
| `USE_EDGE_TTS` | `true` 使用免费 Edge TTS |
| `USE_MIGRATIONS` | `true` 时启动跳过 `create_all()`，需先 `alembic upgrade head` |
| `SKIP_STARTUP_SEED` | `true` 跳过启动 seed |
| `ENABLE_SCHEDULER` | `false` 关闭内置每日场景调度 |

词库中文释义存在 PostgreSQL `dictionary_entries` 表（约 1.2 万词条，数据源 [KyleBing/english-vocabulary](https://github.com/KyleBing/english-vocabulary)）。首次环境执行 `python -m app.cli seed-dictionary`，更新释义后执行 `python -m app.cli seed`。

前端关键配置：

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址，默认 `http://localhost:8000/api` |

## API 文档

启动后端后访问 http://localhost:8000/docs

## 项目结构

```
packages/api-client/   共享 API 客户端
packages/app-core/     共享 React UI
apps/web/              Next.js Web 主线
apps/shell/            Vite SPA（Capacitor/Tauri）
backend/app/           FastAPI 后端
docs/                  扩展文档（含 MONOREPO.md）
```

详见 [docs/MONOREPO.md](docs/MONOREPO.md)。

## 测试

本地测试连接 john-server 的 `english-study-test` 与 `english-study-bucket-test`，详见 [docs/TEST_ENV.md](docs/TEST_ENV.md)。

```bash
cd backend
pytest
```

## 数据库迁移（Alembic）

默认 `.env` 已设置 `USE_MIGRATIONS=true`，启动时自动 `alembic upgrade head`。手动执行：

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

## CLI 数据灌库

启动时可通过 `SKIP_STARTUP_SEED=true` 跳过 seed；独立灌库：

```bash
cd backend
python -m app.cli seed
python -m app.cli daily-scenarios   # 手动触发每日场景
```

多实例部署时建议 `ENABLE_SCHEDULER=false`，由 cron/k8s 调用 `daily-scenarios`。

## 认证说明

当前 MVP 使用 `device_id` 区分学习进度，**非安全认证**。JWT 接口（`/api/auth/*`）为后续多用户预留。

## 扩展

- 多用户：JWT 骨架已就绪，见 `/api/auth/*`
- 本地测试环境（PostgreSQL + MinIO）：见 [docs/TEST_ENV.md](docs/TEST_ENV.md)
- 生产部署（PostgreSQL + MinIO + Portainer）：见 [docs/PORTAINER_DEPLOY.md](docs/PORTAINER_DEPLOY.md)，Stack 文件 [docker-compose.prod.yml](docker-compose.prod.yml)
- 前端 TypeScript 类型可从 `/openapi.json` 生成（暂未引入 codegen 依赖）
