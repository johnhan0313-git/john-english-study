# SceneEnglish — 成人英语场景学习平台

对标 CET-4/6 的成人英语学习网站，以场景化词汇学习为核心，兼顾听说读写，支持 AI 生成场景与练习题。

## 功能

- **词库**：CET-4/6 合并词表（6000+ 词），按主题分组浏览
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
- OpenAI 兼容 API Key（可选，未配置时使用 Mock 数据）

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# 编辑 backend/.env 填入 AI_LLM_API_KEY 等

uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

访问 http://localhost:3000

### Docker

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```

## 环境变量

- 后端：[backend/.env.example](backend/.env.example)
- 前端：[frontend/.env.example](frontend/.env.example)

后端关键配置：

| 变量 | 说明 |
|------|------|
| `AI_LLM_*` / `AI_STT_*` / `AI_TTS_*` | 按能力分别配置 API（可混用 Groq、DeepSeek、OpenAI 等） |
| `USE_EDGE_TTS` | `true` 使用免费 Edge TTS |

前端关键配置：

| 变量 | 说明 |
|------|------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址，默认 `http://localhost:8000/api` |

## API 文档

启动后端后访问 http://localhost:8000/docs

## 项目结构

```
backend/app/     FastAPI 后端
frontend/src/    Next.js 前端
docs/            扩展文档
```

## 测试

```bash
cd backend
pytest
```

## 扩展

- 多用户：JWT 骨架已就绪，见 `/api/auth/*`
- PostgreSQL：见 [docs/POSTGRESQL_MIGRATION.md](docs/POSTGRESQL_MIGRATION.md)
