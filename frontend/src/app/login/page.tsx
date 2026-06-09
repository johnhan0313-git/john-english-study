"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { Button, Card, Input, PageHeader } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";
import { authApi, wechatAuthorizeHref } from "@/lib/auth/api";
import { ApiError } from "@/lib/api";

function parseApiError(err: unknown, fallback: string): string {
  if (!(err instanceof ApiError)) return fallback;
  try {
    const parsed = JSON.parse(err.message) as { detail?: string };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // plain text
  }
  return err.message || fallback;
}

export default function LoginPage() {
  const { loginWithEmail, isAuthenticated } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/";

  const [email, setEmail] = useState("");
  const [captchaCode, setCaptchaCode] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [captchaId, setCaptchaId] = useState("");
  const [captchaSvg, setCaptchaSvg] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);

  const loadCaptcha = useCallback(async () => {
    const data = await authApi.getCaptcha();
    setCaptchaId(data.captcha_id);
    setCaptchaSvg(data.captcha_svg);
    if (data.dev_answer) setCaptchaCode(data.dev_answer);
  }, []);

  useEffect(() => {
    if (isAuthenticated) router.replace(next);
  }, [isAuthenticated, router, next]);

  useEffect(() => {
    loadCaptcha().catch(() => setError("无法加载验证码"));
  }, [loadCaptcha]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setInterval(() => {
      setCooldown((value) => (value > 0 ? value - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  const onSendCode = async () => {
    setError("");
    if (!email.trim()) {
      setError("请输入邮箱");
      return;
    }
    if (!captchaCode.trim()) {
      setError("请输入图形验证码");
      return;
    }
    setSendingCode(true);
    try {
      const result = await authApi.sendEmailCode({
        email: email.trim(),
        captcha_id: captchaId,
        captcha_code: captchaCode.trim(),
      });
      setCooldown(result.cooldown_seconds || 60);
      if (result.dev_code) setEmailCode(result.dev_code);
      await loadCaptcha();
      setCaptchaCode("");
    } catch (err) {
      setError(parseApiError(err, "发送验证码失败"));
      await loadCaptcha();
    } finally {
      setSendingCode(false);
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await loginWithEmail(email.trim(), emailCode.trim());
      router.push(next);
    } catch (err) {
      setError(parseApiError(err, "登录失败"));
    } finally {
      setLoading(false);
    }
  };

  const onWeChatLogin = () => {
    window.location.href = wechatAuthorizeHref(next);
  };

  return (
    <div className="mx-auto max-w-md space-y-6">
      <PageHeader badge="账号" title="登录 / 注册" description="使用邮箱验证码或微信授权登录，首次登录将自动注册" />
      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">邮箱</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">图形验证码</label>
            <div className="flex items-center gap-2">
              <Input
                value={captchaCode}
                onChange={(e) => setCaptchaCode(e.target.value)}
                required
                autoComplete="off"
                placeholder="输入右侧字符"
                className="flex-1"
              />
              <button
                type="button"
                onClick={() => loadCaptcha().catch(() => setError("无法刷新验证码"))}
                className="shrink-0 overflow-hidden rounded border border-slate-200 bg-white"
                title="点击刷新"
                dangerouslySetInnerHTML={{ __html: captchaSvg }}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">邮箱验证码</label>
            <div className="flex gap-2">
              <Input
                value={emailCode}
                onChange={(e) => setEmailCode(e.target.value)}
                required
                autoComplete="one-time-code"
                placeholder="6 位数字"
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                disabled={sendingCode || cooldown > 0}
                onClick={onSendCode}
              >
                {cooldown > 0 ? `${cooldown}s` : sendingCode ? "发送中..." : "获取验证码"}
              </Button>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? "登录中..." : "登录 / 注册"}
          </Button>
        </form>

        <div className="relative my-6">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-slate-500">或</span>
          </div>
        </div>

        <Button type="button" variant="outline" className="w-full" onClick={onWeChatLogin}>
          微信扫码登录
        </Button>
      </Card>
    </div>
  );
}
