import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { HashRouter } from "react-router-dom";

import "@sceneenglish/app-core/styles/globals.css";

import { ShellPlatformProviders } from "./platform/shell-platform";
import { ShellApp } from "./routes";

const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HashRouter>
      <ShellPlatformProviders apiBase={apiBase}>
        <ShellApp />
      </ShellPlatformProviders>
    </HashRouter>
  </StrictMode>,
);
