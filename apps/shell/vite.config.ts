import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@sceneenglish/api-client": path.resolve(__dirname, "../../packages/api-client/src/index.ts"),
      "@sceneenglish/app-core": path.resolve(__dirname, "../../packages/app-core/src"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
