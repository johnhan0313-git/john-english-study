"use client";

import { useNavigate, useSearchParams } from "@sceneenglish/app-core/platform/context";
import { FormEvent, useEffect, useState } from "react";

import { CaptchaModal } from "@sceneenglish/app-core/components/auth/captcha-modal";
import { Button, Card, Input, PageHeader } from "@sceneenglish/app-core/components/ui";
import { useAuth } from "@sceneenglish/app-core/contexts/auth-context";
import { authApi, wechatAuthorizeHref } from "@sceneenglish/api-client";
import { ApiError } from "@sceneenglish/api-client";

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
  const navigate = useNavigate();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") || "/";

  const [email, setEmail] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [codeSent, setCodeSent] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState("");
  const [sendingCode, setSendingCode] = useState(false);
  const [captchaOpen, setCaptchaOpen] = useState(false);
  const [captchaError, setCaptchaError] = useState("");
  const [loggingIn, setLoggingIn] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate(next);
  }, [isAuthenticated, navigate, next]);

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
    setSendingCode(true);
    try {
      const result = await authApi.sendEmailCode({ email: email.trim() });
      setCooldown(result.cooldown_seconds || 60);
      if (result.dev_code) setEmailCode(result.dev_code);
      setCodeSent(true);
    } catch (err) {
      setError(parseApiError(err, "发送验证码失败"));
    } finally {
      setSendingCode(false);
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim()) {
      setError("请输入邮箱");
      return;
    }
    if (!emailCode.trim()) {
      setError("请输入邮箱验证码");
      return;
    }
    setCaptchaError("");
    setCaptchaOpen(true);
  };

  const onCaptchaComplete = async (captchaId: string, captchaX: number) => {
    setCaptchaError("");
    setLoggingIn(true);
    try {
      await loginWithEmail(email.trim(), emailCode.trim(), {
        captcha_id: captchaId,
        captcha_x: captchaX,
      });
      setCaptchaOpen(false);
      navigate(next);
    } catch (err) {
      const message = parseApiError(err, "登录失败");
      if (message.includes("拼图")) {
        setCaptchaError(message);
      } else {
        setCaptchaOpen(false);
        setError(message);
      }
    } finally {
      setLoggingIn(false);
    }
  };

  const onWeChatLogin = () => {
    window.location.href = wechatAuthorizeHref(next);
  };

  return (
    <>
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

            {codeSent && (
              <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">验证码已发送，请查收邮件</p>
            )}

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
                  {cooldown > 0 ? `${cooldown}s` : sendingCode ? "发送中..." : codeSent ? "重新发送" : "获取验证码"}
                </Button>
              </div>
            </div>

            {error && <p className="text-sm text-red-600">{error}</p>}

            <Button type="submit" className="w-full" disabled={loggingIn}>
              {loggingIn ? "登录中..." : "登录 / 注册"}
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

      <CaptchaModal
        open={captchaOpen}
        loading={loggingIn}
        error={captchaError}
        onClose={() => !loggingIn && setCaptchaOpen(false)}
        onComplete={onCaptchaComplete}
      />
    </>
  );
}
