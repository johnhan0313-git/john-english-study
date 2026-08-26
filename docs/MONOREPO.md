# SceneEnglish Monorepo

## 结构

```
packages/api-client   # 传输层 HTTP + DTO（无 UI 展示规则）
packages/app-core     # features/* 垂直切片 + app-chrome + platform
apps/web              # Next.js 薄壳（app/** + platform/**）
apps/shell            # Vite SPA（Capacitor / Electron 共用静态产物）
apps/mobile           # Capacitor（iOS / Android）
apps/desktop          # Electron（macOS / Windows / Linux）
backend/              # FastAPI：domains / application / infrastructure / composition
```

### app-core feature 边界

| Feature | 职责 |
|---------|------|
| `auth` | 登录/注册/回调、token、AuthProvider、RequireAuth |
| `scenarios` / `exercises` | 场景详情、生成、练习工作流 |
| `conversation` | 对话页 + voice-turn（经 platform recorder/audio） |
| `words` / `activity` / `progress` / `profile` / `reference` / `home` | 各自能力 |
| `app-chrome` | Shell、导航、providers、prefetch（非业务 feature） |

Hosts 仅依赖 `@sceneenglish/app-core` 根导出与 `@sceneenglish/app-core/platform/*`。

## 常用命令

```bash
npm install                 # 根目录安装全部 workspace 依赖
npm run build:packages      # api-client + app-core typecheck
npm run dev:web             # Web 开发 http://localhost:3000
npm run dev:shell           # Shell SPA 开发 http://localhost:5173
npm run dev:desktop         # Electron 桌面开发（联动 shell dev server）
npm run build:web           # 构建 Next.js
npm run build:shell         # 构建 shell/dist

# Capacitor（需先 build:shell）
cd apps/mobile && npm run cap:sync

# Electron 桌面端（需先在仓库根目录 npm install）
npm run build:desktop
# 或
cd apps/desktop && npm run build
```

## 本机环境要求

| 目标 | 额外依赖 |
|------|----------|
| Web（`npm run dev:web`） | 无 |
| Shell SPA（`npm run dev:shell`） | 无 |
| Capacitor 移动端 | Xcode / Android Studio（打原生包） |
| **Electron 桌面端** | Node.js 20+（无需 Rust） |

## 环境变量

| 应用 | 变量 | 说明 |
|------|------|------|
| apps/web | `NEXT_PUBLIC_API_URL` | 默认 `http://localhost:8000/api` |
| apps/shell | `VITE_API_URL` | 生产建议 `https://se.cool-app.me/api` |

## 架构门禁

- 后端：`backend/tests/test_architecture_gates.py`（Domain 禁 ORM、ScenarioService/ensure_*/get_or_create 残留扫描）
- 前端：`scripts/check-frontend-architecture.sh`（禁止 apps/web 深路径死代码、禁止 app-core 深导出）

## 小程序（后续）

UI 使用 Taro 新建 `apps/mini`，复用 `@sceneenglish/api-client` 与 platform 接口。

## 后续债

物理 FK 拆除、Outbox、OpenAPI codegen、Conversation/Catalog 全量 Domain 抽取。
