import { ApiError } from "./client";

function detailFromBody(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== "object") return null;
        const msg = (item as { msg?: unknown }).msg;
        return typeof msg === "string" ? msg : null;
      })
      .filter(Boolean);
    if (messages.length) return messages.join("；");
  }
  return null;
}

export function parseApiError(err: unknown, fallback: string): string {
  if (err instanceof TypeError) {
    return "网络请求失败，请检查网络连接或后端服务是否可用";
  }
  if (!(err instanceof ApiError)) return fallback;
  try {
    const parsed = JSON.parse(err.message) as unknown;
    const detail = detailFromBody(parsed);
    if (detail) return detail;
  } catch {
    // plain text
  }
  return err.message || fallback;
}
