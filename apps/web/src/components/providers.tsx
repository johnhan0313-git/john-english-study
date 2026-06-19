"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Suspense, useState } from "react";

import { AuthProvider } from "@/contexts/auth-context";
import { createQueryClient } from "@/lib/query-client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => createQueryClient());
  return (
    <QueryClientProvider client={client}>
      <Suspense fallback={null}>
        <AuthProvider>{children}</AuthProvider>
      </Suspense>
    </QueryClientProvider>
  );
}
