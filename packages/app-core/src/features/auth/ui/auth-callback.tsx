"use client";

import { useNavigate, useSearchParams } from "../../../platform/context";
import { useEffect, useState } from "react";

import { Card, PageHeader } from "../../../app-chrome/ui";
import { useAuth } from "../auth-context";

export default function AuthCallbackPage() {
  const { finishOAuthLogin, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const searchParams = useSearchParams();
  const [error, setError] = useState("");

  useEffect(() => {
    if (isAuthenticated) {
      navigate(searchParams.get("next") || "/", { replace: true });
      return;
    }

    const token = searchParams.get("token");
    const next = searchParams.get("next") || "/";
    if (!token) {
      setError("缺少登录凭证，请重新登录");
      return;
    }

    finishOAuthLogin(token)
      .then(() => navigate(next, { replace: true }))
      .catch(() => setError("登录失败，请重试"));
  }, [finishOAuthLogin, isAuthenticated, navigate, searchParams]);

  return (
    <div className="mx-auto max-w-md space-y-6">
      <PageHeader badge="账号" title="正在登录" description="请稍候，正在完成授权登录..." />
      <Card>
        {error ? <p className="text-sm text-red-600">{error}</p> : <p className="text-sm text-slate-600">处理中...</p>}
      </Card>
    </div>
  );
}
