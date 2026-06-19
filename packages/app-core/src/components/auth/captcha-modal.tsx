"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { X } from "lucide-react";

import { SliderCaptcha } from "@sceneenglish/app-core/components/auth/slider-captcha";
import { authApi, type CaptchaData } from "@sceneenglish/api-client";

interface CaptchaModalProps {
  open: boolean;
  loading?: boolean;
  error?: string;
  onClose: () => void;
  onComplete: (captchaId: string, captchaX: number) => void;
}

export function CaptchaModal({ open, loading, error, onClose, onComplete }: CaptchaModalProps) {
  const [captcha, setCaptcha] = useState<CaptchaData | null>(null);
  const submittingRef = useRef(false);

  const loadCaptcha = useCallback(async () => {
    const data = await authApi.getCaptcha();
    setCaptcha(data);
  }, []);

  useEffect(() => {
    if (!open) return;
    submittingRef.current = false;
    loadCaptcha().catch(() => undefined);
  }, [open, loadCaptcha]);

  useEffect(() => {
    if (!open || !error) return;
    submittingRef.current = false;
    loadCaptcha().catch(() => undefined);
  }, [error, open, loadCaptcha]);

  const handleComplete = (x: number) => {
    if (!captcha || loading || submittingRef.current) return;
    submittingRef.current = true;
    onComplete(captcha.captcha_id, x);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40"
        onClick={() => !loading && onClose()}
        aria-label="关闭"
      />
      <div className="relative z-10 w-full max-w-sm rounded-xl border border-slate-200 bg-white p-5 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-900">安全验证</h3>
          <button type="button" onClick={onClose} disabled={loading} className="text-slate-400 hover:text-slate-600 disabled:opacity-50">
            <X className="h-5 w-5" />
          </button>
        </div>

        {captcha ? (
          <SliderCaptcha
            data={captcha}
            onComplete={handleComplete}
            onRefresh={() => loadCaptcha().catch(() => undefined)}
            disabled={loading}
            error={error}
          />
        ) : (
          <p className="py-8 text-center text-sm text-slate-500">加载验证中...</p>
        )}

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>
    </div>
  );
}
