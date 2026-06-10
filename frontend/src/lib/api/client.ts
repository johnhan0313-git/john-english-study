import { API_BASE } from "@/lib/env";
import { clearAccessToken, getAccessToken } from "@/lib/auth/token";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

function isAuthAttempt(path: string): boolean {
  return path.includes("/auth/email/login") || path.includes("/auth/login");
}

function handleUnauthorized() {
  clearAccessToken();
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("auth:unauthorized"));
  }
}

export function authHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function authFetch(path: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (res.status === 401 && getAccessToken() && !isAuthAttempt(path)) {
    handleUnauthorized();
  }
  return res;
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 401 && getAccessToken() && !isAuthAttempt(path)) {
      handleUnauthorized();
    }
    throw new ApiError(text || res.statusText, res.status);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res as unknown as T;
}

export function apiPathFromUrl(url: string): string {
  if (url.startsWith(API_BASE)) {
    const path = url.slice(API_BASE.length);
    return path.startsWith("/") ? path : `/${path}`;
  }
  if (url.startsWith("/")) return url;
  try {
    const parsed = new URL(url);
    const base = new URL(API_BASE);
    if (parsed.origin === base.origin && parsed.pathname.startsWith(base.pathname)) {
      const prefix = base.pathname.endsWith("/") ? base.pathname.slice(0, -1) : base.pathname;
      const path = parsed.pathname.slice(prefix.length);
      return `${path.startsWith("/") ? path : `/${path}`}${parsed.search}`;
    }
  } catch {
    // ignore malformed url
  }
  return url;
}

export async function fetchAuthenticatedAudioBlobUrl(url: string): Promise<string> {
  const path = apiPathFromUrl(url);
  const res = await authFetch(path);
  if (!res.ok) {
    const text = await res.text();
    let detail = text;
    try {
      const parsed = JSON.parse(text) as { detail?: string };
      if (typeof parsed.detail === "string") detail = parsed.detail;
    } catch {
      // plain text
    }
    throw new ApiError(detail || "语音加载失败", res.status);
  }
  const blob = await res.blob();
  if (!blob.size) throw new ApiError("语音文件为空", res.status);
  return URL.createObjectURL(blob);
}

export { API_BASE };
