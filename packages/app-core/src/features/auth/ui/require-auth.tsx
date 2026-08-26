"use client";

import { useNavigate, useSearchParams } from "../../../platform/context";
import { useEffect } from "react";

import { Spinner } from "../../../app-chrome/ui";
import { useAuth } from "../auth-context";

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
