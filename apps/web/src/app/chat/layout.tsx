"use client";

import { RequireAuth } from "@sceneenglish/app-core";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
