"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { Spinner } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || (typeof window !== "undefined" ? window.location.pathname : "/");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/login?next=${encodeURIComponent(next)}`);
    }
  }, [isLoading, isAuthenticated, router, next]);

  if (isLoading) {
    return <Spinner label="验证登录状态..." />;
  }
  if (!isAuthenticated) {
    return null;
  }
  return <>{children}</>;
}
