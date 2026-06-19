import { request } from "@/lib/api/client";
import { API_BASE } from "@/lib/env";
import type { AuthResponse, AuthUser, MergeDeviceResult } from "./types";

export interface CaptchaData {
  captcha_id: string;
  width: number;
  height: number;
  puzzle_y: number;
  piece_width: number;
  background_svg: string;
  piece_svg: string;
  dev_answer?: string | null;
}

export interface SendCodeResult {
  message: string;
  cooldown_seconds: number;
  dev_code?: string | null;
}

export const authApi = {
  getCaptcha: () => request<CaptchaData>("/auth/captcha"),

  sendEmailCode: (body: { email: string }) =>
    request<SendCodeResult>("/auth/email/send-code", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  emailLogin: (body: { email: string; code: string; captcha_id: string; captcha_x: number }) =>
    request<AuthResponse>("/auth/email/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => request<AuthUser>("/auth/me"),

  mergeDevice: (device_id: string) =>
    request<MergeDeviceResult>("/auth/merge-device", {
      method: "POST",
      body: JSON.stringify({ device_id }),
    }),
};

export function wechatAuthorizeHref(nextPath = "/"): string {
  const params = new URLSearchParams({ next: nextPath });
  return `${API_BASE}/auth/wechat/authorize?${params.toString()}`;
}
