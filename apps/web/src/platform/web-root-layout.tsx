import type { ReactNode } from "react";

import { AppShell } from "@sceneenglish/app-core";

import { WebPlatformProviders } from "../platform/web-platform";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export function WebRootLayout({ children }: { children: ReactNode }) {
  return (
    <WebPlatformProviders apiBase={API_BASE}>
      <AppShell>{children}</AppShell>
    </WebPlatformProviders>
  );
}
