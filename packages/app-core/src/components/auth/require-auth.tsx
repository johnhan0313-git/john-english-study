"use client";

import { useNavigate, useSearchParams } from "@sceneenglish/app-core/platform/context";
import { useEffect } from "react";

import { Spinner } from "@sceneenglish/app-core/components/ui";
import { useAuth } from "@sceneenglish/app-core/contexts/auth-context";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || (typeof window !== "undefined" ? window.location.pathname : "/");

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate(`/login?next=${encodeURIComponent(next)}`);
    }
  }, [isLoading, isAuthenticated, navigate, next]);

  if (isLoading) {
    return <Spinner label="验证登录状态..." />;
  }
  if (!isAuthenticated) {
    return null;
  }
  return <>{children}</>;
}
