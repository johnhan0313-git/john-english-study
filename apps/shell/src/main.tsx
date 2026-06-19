import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import "@sceneenglish/app-core/styles/globals.css";

import { ShellPlatformProviders } from "./platform/shell-platform";
import { ShellApp } from "./routes";

const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ShellPlatformProviders apiBase={apiBase}>
        <ShellApp />
      </ShellPlatformProviders>
    </BrowserRouter>
  </StrictMode>,
);
