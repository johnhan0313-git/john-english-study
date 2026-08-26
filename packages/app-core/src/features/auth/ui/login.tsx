"use client";

import { useNavigate, useSearchParams } from "../../../platform/context";
import { FormEvent, useEffect, useState } from "react";

import { Button, Card, Input, PageHeader } from "../../../app-chrome/ui";
import { useAuth } from "../auth-context";
import { authApi, parseApiError } from "@sceneenglish/api-client";
import { authCopy, authErrors, authValidation } from "../model";

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
      setError(authValidation.emailRequired);
      return;
    }
    setSendingCode(true);
    try {
      const result = await authApi.sendEmailCode({ email: email.trim() });
      setCooldown(result.cooldown_seconds || 60);
      if (result.dev_code) setEmailCode(result.dev_code);
      setCodeSent(true);
    } catch (err) {
      setError(parseApiError(err, authErrors.sendCodeFailed));
    } finally {
      setSendingCode(false);
    }
  };

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    if (!email.trim()) {
      setError(authValidation.emailRequired);
      return;
    }
    if (!emailCode.trim()) {
      setError(authValidation.emailCodeRequired);
      return;
    }
    setLoggingIn(true);
    try {
      await loginWithEmail(email.trim(), emailCode.trim());
      navigate(next);
    } catch (err) {
      setError(parseApiError(err, authErrors.loginFailed));
    } finally {
      setLoggingIn(false);
    }
  };

  return (
    <div className="mx-auto max-w-md space-y-6">
      <PageHeader
        badge={authCopy.pageBadge}
        title={authCopy.pageTitle}
        description={authCopy.pageDescription}
      />
      <Card>
        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{authCopy.emailLabel}</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder={authCopy.emailPlaceholder}
            />
          </div>

          {codeSent && (
            <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{authCopy.codeSentHint}</p>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">{authCopy.emailCodeLabel}</label>
            <div className="flex gap-2">
              <Input
                value={emailCode}
                onChange={(e) => setEmailCode(e.target.value)}
                required
                autoComplete="one-time-code"
                placeholder={authCopy.emailCodePlaceholder}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                disabled={sendingCode || cooldown > 0}
                onClick={onSendCode}
              >
                {cooldown > 0
                  ? `${cooldown}s`
                  : sendingCode
                    ? authCopy.sendingCode
                    : codeSent
                      ? authCopy.resendCode
                      : authCopy.sendCode}
              </Button>
            </div>
          </div>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <Button type="submit" className="w-full" disabled={loggingIn}>
            {loggingIn ? authCopy.submitting : authCopy.submit}
          </Button>
        </form>
      </Card>
    </div>
  );
}
