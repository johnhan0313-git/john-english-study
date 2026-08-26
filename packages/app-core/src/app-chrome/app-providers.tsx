"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Suspense, useState, type ReactNode } from "react";

import { AuthProvider } from "../features/auth";
import { createQueryClient } from "./query-client";
import { PlatformProvider } from "../platform/context";
import type { PlatformServices } from "../platform/types";

export function AppProviders({
  platform,
  children,
}: {
  platform: PlatformServices;
  children: ReactNode;
}) {
  const [client] = useState(() => createQueryClient());
  return (
    <PlatformProvider platform={platform}>
      <QueryClientProvider client={client}>
        <Suspense fallback={null}>
          <AuthProvider>{children}</AuthProvider>
        </Suspense>
      </QueryClientProvider>
    </PlatformProvider>
  );
}
