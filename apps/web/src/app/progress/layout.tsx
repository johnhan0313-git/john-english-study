"use client";

import { RequireAuth } from "@sceneenglish/app-core";

export default function ProgressLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
