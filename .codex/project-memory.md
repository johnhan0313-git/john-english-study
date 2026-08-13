# SceneEnglish 项目记忆

## 项目定位

SceneEnglish（仓库名 `john-english-study`）是成人英语场景学习平台。核心体验是按 CET-4/6、PETS 等词库生成带目标词汇的英语场景，并提供练习、听力、口语评测、翻译、写作/对话与学习进度。

## 仓库结构与边界

- `backend/`：Python 3.11+、FastAPI、SQLAlchemy、Alembic。业务代码位于 `backend/app/`。
- `packages/api-client/`：纯 TypeScript API 请求封装、类型和领域 API；Web/Shell 共用。
- `packages/app-core/`：共享 React 页面、组件、认证上下文、平台抽象和 hooks；不直接绑定浏览器/原生运行时。
- `apps/web/`：Next.js Web 主线，使用 `@sceneenglish/api-client` 与 `@sceneenglish/app-core`。
- `apps/shell/`：Vite + React 的 HashRouter SPA，供 Capacitor 和 Electron 复用。
- `apps/mobile/`：Capacitor 原生工程配置。
- `apps/desktop/`：Electron 主进程与打包资源。
- `backend/data/`：本地媒体和 seed 数据；生产/测试媒体通常走 MinIO。
- `docs/`：monorepo、测试环境、Portainer 部署说明。

## 后端启动与请求链路

入口是 `backend/app/main.py` 的 `app`。应用 lifespan 会：配置日志、初始化数据库、检查 LLM/STT/TTS、按配置执行参考资料和词库 seed、启动每日场景 APScheduler。生产/迁移环境用 `USE_MIGRATIONS=true` 时先执行 Alembic；开发 SQLite 可由 `create_all()` 初始化。

路由统一挂在 `/api`：`common`、`auth`、`profile`、`words`、`scenarios`、`scenario_complete`、`exercises`、`progress`、`reference`、`conversations`、`activity`。场景生成和每日场景由 `ScenarioService` 驱动，AI 能力位于 `services/ai`，词汇/SRS 位于 `services/vocabulary`，音频/TTS 位于 `services/media`。

## 前端运行方式

- Web：`NEXT_PUBLIC_API_URL`，默认 `http://localhost:8000/api`。
- Shell：`VITE_API_URL`，默认 `http://localhost:8000/api`；入口使用 `HashRouter` 和 `ShellPlatformProviders`。
- API client 通过统一 `request()` / `authFetch()` 注入 Bearer token，收到受保护请求的 401 时调用 `onUnauthorized`。
- 页面路由和平台差异主要在 `packages/app-core/src/platform`、`apps/shell/src/routes.tsx` 及 Web 壳中维护。

## 常用命令

```bash
npm install
./run.sh start                 # Web :3000 + API :8000
./run.sh stop
npm run dev:web
npm run dev:shell
npm run build:web
npm run build:shell
npm run build:packages
cd backend && source .venv/bin/activate && pytest
```

## 环境与数据约束

复制 `backend/.env.example` 和 `apps/web/.env.example` 后再启动。默认测试环境通过 Tailscale 访问 john-server 的 PostgreSQL 和 MinIO；测试资源必须是数据库 `english-study-test`、bucket `english-study-bucket-test`，禁止把本地测试 `.env` 指向生产资源。生产部署见 `docker-compose.prod.yml` 和 `docs/PORTAINER_DEPLOY.md`。

关键后端配置：`DATABASE_URL`、`STORAGE_BACKEND`/`S3_*`、`AI_LLM_*`、`AI_STT_*`、`AI_TTS_*`、`USE_EDGE_TTS`、`USE_MIGRATIONS`、`SKIP_STARTUP_SEED`、`ENABLE_SCHEDULER`。未配置 LLM 时场景生成使用 Mock；未配置 STT 时口语评测退回期望文本；Edge TTS 默认开启。

词库释义在 PostgreSQL `dictionary_entries`；需要时运行 `python -m app.cli seed-dictionary`，再运行 `python -m app.cli seed`。多实例部署建议关闭内置 scheduler，由 cron/k8s 调用 `daily-scenarios`。

## 认证现状

学习进度历史上以 `device_id` 区分，当前 MVP 不是安全认证；JWT、邮箱 OTP、微信 OAuth 的 `/api/auth/*` 骨架已存在并逐步接入。涉及用户数据的 API 默认通过 `get_current_user` 依赖；改认证时需同时检查前端 auth context、token 存储和测试 helper。

## 测试注意事项

测试配置由 `backend/tests` 读取，并会校验 `-test` 数据库/bucket。PostgreSQL 测试按用例清理业务表，seed 表通常只灌一次；MinIO 测试 bucket 会清空。修改模型/API/seed 时优先补对应 `backend/tests/test_*.py`，并注意 SQLite 与 PostgreSQL 行为差异。

## 维护约定

优先复用 `api-client`、`app-core` 和现有 service/schema 模式，不在各端重复实现 API。涉及媒体时同时确认本地存储与 S3 响应路径；涉及时间/每日场景时使用 `app_timezone` 和 `app.utils.time`。启动问题先看 `.run/backend.log`、`.run/frontend.log` 及 `/docs` OpenAPI。
