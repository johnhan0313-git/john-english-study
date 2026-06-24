import { request } from "../client";
import { API_BASE } from "../client";
import type { AuthResponse, AuthUser, MergeDeviceResult } from "./types";

export interface SendCodeResult {
  message: string;
  cooldown_seconds: number;
  dev_code?: string | null;
}

export const authApi = {
  sendEmailCode: (body: { email: string }) =>
    request<SendCodeResult>("/auth/email/send-code", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  emailLogin: (body: { email: string; code: string }) =>
    request<AuthResponse>("/auth/email/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => request<AuthUser>("/auth/me"),

  mergeDevice: (device_id: string) =>
    request<MergeDeviceResult>("/auth/merge-device", {
      method: "POST",
      body: JSON.stringify({ device_id }),
    }),
};

export function wechatAuthorizeHref(nextPath = "/", platform: "web" | "app" = "web"): string {
  const params = new URLSearchParams({ next: nextPath, platform });
  return `${API_BASE}/auth/wechat/authorize?${params.toString()}`;
}
