import { getApiBase, getApiClientConfig } from "./config";

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

function handleUnauthorized(): void {
  getApiClientConfig().onUnauthorized?.();
}

export function authHeaders(): HeadersInit {
  const token = getApiClientConfig().getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function authFetch(path: string, options?: RequestInit): Promise<Response> {
  const base = getApiBase();
  const token = getApiClientConfig().getToken();
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (res.status === 401 && token && !isAuthAttempt(path)) {
    handleUnauthorized();
  }
  return res;
}

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const base = getApiBase();
  const token = getApiClientConfig().getToken();
  const res = await fetch(`${base}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 401 && token && !isAuthAttempt(path)) {
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
  const API_BASE = getApiBase();
  if (url.startsWith(API_BASE)) {
    const path = url.slice(API_BASE.length);
    return path.startsWith("/") ? path : `/${path}`;
  }
  if (url.startsWith("/")) return url;
  const origin = getApiClientConfig().getOrigin?.() ?? "http://localhost";
  try {
    if (API_BASE.startsWith("/")) {
      const parsed = new URL(url, origin);
      const prefix = API_BASE.endsWith("/") ? API_BASE.slice(0, -1) : API_BASE;
      if (parsed.pathname.startsWith(prefix)) {
        const path = parsed.pathname.slice(prefix.length);
        return `${path.startsWith("/") ? path : `/${path}`}${parsed.search}`;
      }
    } else {
      const parsed = new URL(url);
      const base = new URL(API_BASE);
      if (parsed.origin === base.origin && parsed.pathname.startsWith(base.pathname)) {
        const prefix = base.pathname.endsWith("/") ? base.pathname.slice(0, -1) : base.pathname;
        const path = parsed.pathname.slice(prefix.length);
        return `${path.startsWith("/") ? path : `/${path}`}${parsed.search}`;
      }
    }
  } catch {
    // ignore malformed url
  }
  return url;
}

export { getApiBase as API_BASE };
