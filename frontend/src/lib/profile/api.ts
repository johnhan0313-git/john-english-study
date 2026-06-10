import { authFetch } from "@/lib/api/client";
import { API_BASE } from "@/lib/env";
import { request } from "@/lib/api/client";

export interface Profile {
  id: number;
  username: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  oauth_provider: string | null;
  created_at: string;
}

export interface SendEmailChangeCodeResult {
  message: string;
  cooldown_seconds: number;
  dev_code?: string | null;
}

export const profileApi = {
  get: () => request<Profile>("/profile"),

  updateDisplayName: (display_name: string) =>
    request<Profile>("/profile", {
      method: "PATCH",
      body: JSON.stringify({ display_name }),
    }),

  sendEmailChangeCode: (new_email: string) =>
    request<SendEmailChangeCodeResult>("/profile/email/send-code", {
      method: "POST",
      body: JSON.stringify({ new_email }),
    }),

  changeEmail: (new_email: string, code: string) =>
    request<Profile>("/profile/email", {
      method: "PATCH",
      body: JSON.stringify({ new_email, code }),
    }),

  uploadAvatar: async (file: File): Promise<Profile> => {
    const form = new FormData();
    form.append("file", file);
    const res = await authFetch("/profile/avatar", { method: "POST", body: form });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || res.statusText);
    }
    return res.json();
  },
};

export function resolveAvatarUrl(avatarUrl: string | null | undefined): string {
  if (!avatarUrl) return "/avatars/default.svg";
  if (avatarUrl.startsWith("http")) return avatarUrl;
  return `${API_BASE}${avatarUrl}`;
}
