"use client";

import { RequireAuth } from "@sceneenglish/app-core";

export default function ProfileLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
