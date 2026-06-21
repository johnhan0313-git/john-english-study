# SceneEnglish Monorepo

## 结构

```
packages/api-client   # 纯 TS API 客户端（Web / Shell / 未来小程序共用）
packages/app-core     # React UI + platform 抽象
apps/web              # Next.js Web 主线（Docker standalone）
apps/shell            # Vite SPA（Capacitor / Electron 共用静态产物）
apps/mobile           # Capacitor（iOS / Android）
apps/desktop          # Electron（macOS / Windows / Linux）
backend/              # FastAPI
```

## 常用命令

```bash
npm install                 # 根目录安装全部 workspace 依赖
npm run dev:web             # Web 开发 http://localhost:3000
npm run dev:shell           # Shell SPA 开发 http://localhost:5173
npm run dev:desktop         # Electron 桌面开发（联动 shell dev server）
npm run build:web           # 构建 Next.js
npm run build:shell         # 构建 shell/dist

# Capacitor（需先 build:shell）
cd apps/mobile && npm run cap:sync

# Electron 桌面端（需先 build:shell 或使用 npm run dev:desktop）
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

## 小程序（后续）

UI 使用 Taro 新建 `apps/mini`，复用 `@sceneenglish/api-client` 与 platform 接口；详见计划文档。
