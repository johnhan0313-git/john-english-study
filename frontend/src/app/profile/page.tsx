"use client";

import { useEffect, useRef, useState } from "react";
import { Camera } from "lucide-react";

import { Button, Input } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";
import { profileApi, resolveAvatarUrl } from "@/lib/profile/api";

function parseApiError(err: unknown, fallback: string): string {
  if (!(err instanceof ApiError) && !(err instanceof Error)) return fallback;
  const message = err instanceof ApiError ? err.message : err.message;
  try {
    const parsed = JSON.parse(message) as { detail?: string };
    if (typeof parsed.detail === "string") return parsed.detail;
  } catch {
    // plain text
  }
  return message || fallback;
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function loginMethodLabel(provider: string | null | undefined) {
  if (provider === "wechat") return "微信登录";
  return "邮箱登录";
}

function ProfileRow({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-2 px-5 py-4 sm:flex-row sm:items-center sm:gap-4", className)}>
      <span className="w-16 shrink-0 text-sm text-slate-500">{label}</span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);

  const [displayName, setDisplayName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [editingEmail, setEditingEmail] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const [feedback, setFeedback] = useState<{ type: "error" | "success"; text: string } | null>(null);
  const [savingName, setSavingName] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [sendingCode, setSendingCode] = useState(false);
  const [changingEmail, setChangingEmail] = useState(false);

  useEffect(() => {
    if (user) setDisplayName(user.display_name || user.username);
  }, [user]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setInterval(() => {
      setCooldown((v) => (v > 0 ? v - 1 : 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 3000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  const showError = (text: string) => setFeedback({ type: "error", text });
  const showSuccess = (text: string) => setFeedback({ type: "success", text });

  const onSaveName = async () => {
    setSavingName(true);
    try {
      await profileApi.updateDisplayName(displayName.trim());
      await refreshUser();
      showSuccess("昵称已保存");
    } catch (err) {
      showError(parseApiError(err, "保存昵称失败"));
    } finally {
      setSavingName(false);
    }
  };

  const onAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingAvatar(true);
    try {
      await profileApi.uploadAvatar(file);
      await refreshUser();
      showSuccess("头像已更新");
    } catch (err) {
      showError(parseApiError(err, "上传头像失败"));
    } finally {
      setUploadingAvatar(false);
      e.target.value = "";
    }
  };

  const onSendEmailCode = async () => {
    if (!newEmail.trim()) {
      showError("请输入新邮箱");
      return;
    }
    setSendingCode(true);
    try {
      const result = await profileApi.sendEmailChangeCode(newEmail.trim());
      setCooldown(result.cooldown_seconds || 60);
      if (result.dev_code) setEmailCode(result.dev_code);
      showSuccess("验证码已发送");
    } catch (err) {
      showError(parseApiError(err, "发送验证码失败"));
    } finally {
      setSendingCode(false);
    }
  };

  const onChangeEmail = async () => {
    if (!newEmail.trim() || !emailCode.trim()) {
      showError("请填写新邮箱和验证码");
      return;
    }
    setChangingEmail(true);
    try {
      await profileApi.changeEmail(newEmail.trim(), emailCode.trim());
      await refreshUser();
      setNewEmail("");
      setEmailCode("");
      setEditingEmail(false);
      showSuccess("邮箱已更新");
    } catch (err) {
      showError(parseApiError(err, "修改邮箱失败"));
    } finally {
      setChangingEmail(false);
    }
  };

  const cancelEmailEdit = () => {
    setEditingEmail(false);
    setNewEmail("");
    setEmailCode("");
  };

  if (!user) return null;

  const avatarSrc = resolveAvatarUrl(user.avatar_url);
  const savedName = user.display_name || user.username;
  const nameDirty = displayName.trim() !== savedName;

  return (
    <div className="mx-auto max-w-md">
      <h1 className="mb-5 text-lg font-semibold text-slate-900">个人中心</h1>

      {feedback && (
        <p
          className={cn(
            "mb-4 text-center text-sm",
            feedback.type === "error" ? "text-red-600" : "text-emerald-600",
          )}
        >
          {feedback.text}
        </p>
      )}

      <div className="overflow-hidden rounded-2xl border border-surface-border/80 bg-white shadow-sm">
        <div className="flex flex-col items-center px-5 pb-6 pt-8">
          <button
            type="button"
            disabled={uploadingAvatar}
            onClick={() => fileRef.current?.click()}
            className="group relative h-20 w-20 overflow-hidden rounded-full ring-2 ring-slate-100 transition hover:ring-brand-200 disabled:opacity-60"
            aria-label="更换头像"
          >
            <img src={avatarSrc} alt="" className="h-full w-full object-cover" />
            <span className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition group-hover:opacity-100">
              <Camera className="h-5 w-5 text-white" />
            </span>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={onAvatarChange}
          />
          <p className="mt-3 text-base font-medium text-slate-900">{savedName}</p>
          <p className="mt-1 text-xs text-slate-400">
            @{user.username} · {loginMethodLabel(user.oauth_provider)} · {formatDate(user.created_at)} 加入
          </p>
        </div>

        <div className="divide-y divide-surface-border/60 border-t border-surface-border/60">
          <ProfileRow label="昵称">
            <div className="flex gap-2">
              <Input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                maxLength={32}
                className="flex-1"
              />
              {nameDirty && (
                <Button type="button" size="sm" disabled={savingName} onClick={onSaveName}>
                  {savingName ? "..." : "保存"}
                </Button>
              )}
            </div>
          </ProfileRow>

          <div>
            <div className="flex items-center gap-4 px-5 py-4">
              <span className="w-16 shrink-0 text-sm text-slate-500">邮箱</span>
              <span className="min-w-0 flex-1 truncate text-sm text-slate-800">
                {user.email || "未绑定"}
              </span>
              <button
                type="button"
                onClick={() => (editingEmail ? cancelEmailEdit() : setEditingEmail(true))}
                className="shrink-0 text-sm text-brand-600 hover:text-brand-700"
              >
                {editingEmail ? "取消" : "修改"}
              </button>
            </div>

            {editingEmail && (
              <div className="space-y-3 border-t border-surface-border/40 bg-slate-50/60 px-5 py-4">
                <div>
                  <label htmlFor="new-email" className="mb-1.5 block text-xs font-medium text-slate-500">
                    新邮箱
                  </label>
                  <Input
                    id="new-email"
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="name@example.com"
                    autoComplete="email"
                  />
                </div>
                <div>
                  <label htmlFor="email-code" className="mb-1.5 block text-xs font-medium text-slate-500">
                    验证码
                  </label>
                  <div className="flex gap-2">
                    <Input
                      id="email-code"
                      value={emailCode}
                      onChange={(e) => setEmailCode(e.target.value)}
                      placeholder="6 位数字"
                      autoComplete="one-time-code"
                      inputMode="numeric"
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="shrink-0"
                      disabled={sendingCode || cooldown > 0}
                      onClick={onSendEmailCode}
                    >
                      {cooldown > 0 ? `${cooldown}s` : "获取验证码"}
                    </Button>
                  </div>
                </div>
                <div className="flex justify-end pt-1">
                  <Button type="button" size="sm" disabled={changingEmail} onClick={onChangeEmail}>
                    {changingEmail ? "保存中..." : "确认更换"}
                  </Button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
