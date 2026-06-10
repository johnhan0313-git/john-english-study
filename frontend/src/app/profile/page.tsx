"use client";

import { useEffect, useRef, useState } from "react";
import Image from "next/image";

import { Button, Card, Input, PageHeader } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";
import { ApiError } from "@/lib/api";
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
    month: "long",
    day: "numeric",
  });
}

function loginMethodLabel(provider: string | null | undefined) {
  if (provider === "wechat") return "微信";
  return "邮箱";
}

export default function ProfilePage() {
  const { user, logout, refreshUser } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);

  const [displayName, setDisplayName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [emailCode, setEmailCode] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
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

  const onSaveName = async () => {
    setError("");
    setSuccess("");
    setSavingName(true);
    try {
      await profileApi.updateDisplayName(displayName.trim());
      await refreshUser();
      setSuccess("昵称已保存");
    } catch (err) {
      setError(parseApiError(err, "保存昵称失败"));
    } finally {
      setSavingName(false);
    }
  };

  const onPickAvatar = () => fileRef.current?.click();

  const onAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError("");
    setSuccess("");
    setUploadingAvatar(true);
    try {
      await profileApi.uploadAvatar(file);
      await refreshUser();
      setSuccess("头像已更新");
    } catch (err) {
      setError(parseApiError(err, "上传头像失败"));
    } finally {
      setUploadingAvatar(false);
      e.target.value = "";
    }
  };

  const onSendEmailCode = async () => {
    setError("");
    setSuccess("");
    if (!newEmail.trim()) {
      setError("请输入新邮箱");
      return;
    }
    setSendingCode(true);
    try {
      const result = await profileApi.sendEmailChangeCode(newEmail.trim());
      setCooldown(result.cooldown_seconds || 60);
      if (result.dev_code) setEmailCode(result.dev_code);
      setSuccess("验证码已发送到新邮箱");
    } catch (err) {
      setError(parseApiError(err, "发送验证码失败"));
    } finally {
      setSendingCode(false);
    }
  };

  const onChangeEmail = async () => {
    setError("");
    setSuccess("");
    if (!newEmail.trim() || !emailCode.trim()) {
      setError("请填写新邮箱和验证码");
      return;
    }
    setChangingEmail(true);
    try {
      await profileApi.changeEmail(newEmail.trim(), emailCode.trim());
      await refreshUser();
      setNewEmail("");
      setEmailCode("");
      setSuccess("邮箱已更新");
    } catch (err) {
      setError(parseApiError(err, "修改邮箱失败"));
    } finally {
      setChangingEmail(false);
    }
  };

  if (!user) return null;

  const avatarSrc = resolveAvatarUrl(user.avatar_url);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader badge="账号" title="个人中心" description="管理头像、昵称与绑定邮箱" />

      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-emerald-600">{success}</p>}

      <Card>
        <h2 className="font-semibold">头像</h2>
        <div className="mt-4 flex items-center gap-4">
          <div className="relative h-20 w-20 overflow-hidden rounded-full border border-slate-200 bg-slate-50">
            <Image src={avatarSrc} alt="头像" fill className="object-cover" unoptimized={avatarSrc.startsWith("http")} />
          </div>
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={onAvatarChange}
            />
            <Button type="button" variant="outline" size="sm" disabled={uploadingAvatar} onClick={onPickAvatar}>
              {uploadingAvatar ? "上传中..." : "选择图片"}
            </Button>
            <p className="mt-1 text-xs text-slate-500">JPG / PNG / WebP，最大 2MB</p>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="font-semibold">基本信息</h2>
        <dl className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">用户名</dt>
            <dd>{user.username}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">注册时间</dt>
            <dd>{formatDate(user.created_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">登录方式</dt>
            <dd>{loginMethodLabel(user.oauth_provider)}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h2 className="font-semibold">昵称</h2>
        <div className="mt-4 flex gap-2">
          <Input
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={32}
            className="flex-1"
          />
          <Button type="button" disabled={savingName} onClick={onSaveName}>
            {savingName ? "保存中..." : "保存昵称"}
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="font-semibold">邮箱</h2>
        <p className="mt-2 text-sm text-slate-600">
          当前邮箱：{user.email || "未绑定"}
        </p>
        <div className="mt-4 space-y-3">
          <Input
            type="email"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            placeholder="新邮箱地址"
            autoComplete="email"
          />
          <div className="flex gap-2">
            <Input
              value={emailCode}
              onChange={(e) => setEmailCode(e.target.value)}
              placeholder="6 位验证码"
              autoComplete="one-time-code"
              className="flex-1"
            />
            <Button type="button" variant="outline" disabled={sendingCode || cooldown > 0} onClick={onSendEmailCode}>
              {cooldown > 0 ? `${cooldown}s` : sendingCode ? "发送中..." : "获取验证码"}
            </Button>
          </div>
          <Button type="button" disabled={changingEmail} onClick={onChangeEmail}>
            {changingEmail ? "更新中..." : "确认修改邮箱"}
          </Button>
        </div>
      </Card>

      <Card>
        <h2 className="font-semibold">账号操作</h2>
        <Button type="button" variant="outline" className="mt-4" onClick={logout}>
          退出登录
        </Button>
      </Card>
    </div>
  );
}
