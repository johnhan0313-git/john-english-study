import { ApiError, apiPathFromUrl, authFetch } from "@sceneenglish/api-client";

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
