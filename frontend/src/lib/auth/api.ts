import { request } from "@/lib/api/client";
import type { AuthResponse, AuthUser, MergeDeviceResult } from "./types";

export const authApi = {
  register: (body: { username: string; password: string; email?: string }) =>
    request<AuthResponse>("/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { username: string; password: string }) =>
    request<AuthResponse>("/auth/login", { method: "POST", body: JSON.stringify(body) }),

  me: () => request<AuthUser>("/auth/me"),

  mergeDevice: (device_id: string) =>
    request<MergeDeviceResult>("/auth/merge-device", {
      method: "POST",
      body: JSON.stringify({ device_id }),
    }),
};
