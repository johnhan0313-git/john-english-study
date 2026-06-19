"use client";

import { RequireAuth } from "@sceneenglish/app-core/components/auth/require-auth";

export default function ProgressLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
