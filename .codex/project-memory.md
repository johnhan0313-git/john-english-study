# SceneEnglish 项目记忆

## 项目定位

SceneEnglish（仓库名 `john-english-study`）是成人英语场景学习平台。核心体验是按 CET-4/6、PETS 等词库生成带目标词汇的英语场景，并提供练习、听力、口语评测、翻译、写作/对话与学习进度。

## 仓库结构与边界

- `backend/`：Python 3.11+、FastAPI。目标依赖方向：Entry → Application → Domain → Port → Infrastructure。
  - `app/domains/`：聚合与 Repository Protocol（无 ORM）
  - `app/application/`：Command/Query + UoW 编排
  - `app/infrastructure/`：SQLAlchemy Repository、UoW、Ability 适配
  - `app/composition/`：进程级 Container（`shared_composition.py`）
  - `app/services/`：尚未完全迁完的遗留服务（conversation / vocabulary import 等），新写路径优先走 Application
- `packages/api-client/`：纯 TypeScript 传输层（HTTP + DTO）；不含 UI 展示规则
- `packages/app-core/`：按 feature 垂直切片（`features/*`）+ `app-chrome` + `platform`
- `apps/web/`：Next.js 薄壳（仅 `app/**` + `platform/**`）
- `apps/shell/`：Vite HashRouter SPA（Capacitor / Electron）
- `backend/data/`：唯一 seed 真相源（词库 JSON、词典、本地 media）

## 后端启动与请求链路

入口是 `backend/app/main.py` 的 `app`。lifespan：日志 → `init_db()` → `init_container()` → 可选 seed → APScheduler。

已迁 Application 的主路径：

- Scenario：`GenerateScenario` / `CreateMissingDailySlots` / Query / Translate（无 `ScenarioService` / `ensure_daily_scenarios`）
- Exercise submit / batch：`ExerciseApplication` + `ProgressApplication`（单次 UoW commit）
- Activity：只读 Query
- Identity：`LoginOrRegisterByEmail/WeChat`（无 `get_or_create_user_*`）
- Media：`materialize_*_audio`（无 `ensure_*_audio` / `tts_facade`）

路由仍挂在 `/api`。跨上下文 Progress 由 Application 协调；Conversation 结束时在同一 session 内写 SRS（不再中途二次 commit）。

## 前端运行方式

- Web：`NEXT_PUBLIC_API_URL`，默认 `http://localhost:8000/api`
- Shell：`VITE_API_URL`；`HashRouter` + `ShellPlatformProviders`
- Hosts 只从 `@sceneenglish/app-core` 根导出取页面 / chrome；禁止深导入 `./pages/*`
- 语音走 `PlatformServices.recorder` / `audio`（`createMediaRecorderAdapter`）

## 常用命令

```bash
npm install
./run.sh start
npm run build:packages
cd backend && source .venv/bin/activate && pytest
pytest tests/test_architecture_gates.py   # DDD 架构门禁
```

## 环境与数据约束

复制 `backend/.env.example` 和 `apps/web/.env.example`。测试资源必须是 `-test` 库/bucket。Seed：`python -m app.cli seed`；词典：`seed-dictionary`。每日场景：`daily-scenarios` CLI 或 Scheduler → `CreateMissingDailySlots`。

## 认证

邮箱 OTP / 微信 OAuth 走 Identity Application；JWT + `get_current_user`。前端 auth 状态仅由 `features/auth` 拥有。

## 后续债（本轮明确不做）

- 实体表物理 FK → 逻辑引用
- Transactional Outbox / MQ
- OpenAPI codegen
- Conversation / Catalog 全量 Domain 抽取
- 小程序 Taro

## 维护约定

优先扩 Application/Domain，不在各端重复 API；媒体同时确认本地与 S3；时间用 `app.utils.time`。架构回归见 `backend/tests/test_architecture_gates.py`。
