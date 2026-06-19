# Capacitor 图标

桌面端图标已由 `npx tauri icon` 生成在 `apps/desktop/src-tauri/icons/`（含 `android/`、`ios/` 子目录）。

首次添加原生工程后，可将对应资源复制进 Capacitor 工程，或使用官方工具：

```bash
npm run build:shell
# 将 apps/web/src/app/icon.svg 作为 1024x1024 源图（可用设计工具导出 PNG）
npx @capacitor/assets generate --iconPath ../../apps/desktop/src-tauri/icons/icon.png
```

`cap add ios` / `cap add android` 之后于 `apps/mobile` 目录执行上述命令。
