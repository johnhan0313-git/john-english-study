import { getApiBase } from "../config";
import { ApiError, authFetch, authHeaders, request } from "../client";
import type { ConversationDetail, ConversationListResponse, ConversationSummary, VoiceTurnResponse } from "./types";

export const conversationsApi = {
  createConversation: (body: {
    scenario_id?: number;
    level?: string;
    theme?: string;
    word_count?: number;
    show_chinese_hint?: boolean;
  }) =>
    request<ConversationDetail>("/conversations", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listConversations: (page = 1, pageSize = 20) =>
    request<ConversationListResponse>(`/conversations?page=${page}&page_size=${pageSize}`),

  getConversation: (id: number) => request<ConversationDetail>(`/conversations/${id}`),

  updateConversationSettings: (id: number, body: { show_chinese_hint: boolean }) =>
    request<ConversationDetail>(`/conversations/${id}/settings`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  endConversation: (id: number) =>
    request<ConversationSummary>(`/conversations/${id}/end`, {
      method: "POST",
      body: JSON.stringify({}),
    }),

  getConversationMessageAudioUrl: (sessionId: number, messageId: number) =>
    `${getApiBase()}/conversations/${sessionId}/messages/${messageId}/audio`,

  async streamConversationMessage(
    sessionId: number,
    content: string,
    showChineseHint: boolean,
    handlers: {
      onToken: (token: string) => void;
      onDone: (messageId: number) => void;
      onError: (message: string) => void;
    },
  ) {
    const res = await authFetch(`/conversations/${sessionId}/messages/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content, show_chinese_hint: showChineseHint }),
    });
    if (!res.ok) {
      handlers.onError((await res.text()) || res.statusText);
      return;
    }
    const reader = res.body?.getReader();
    if (!reader) {
      handlers.onError("Streaming not supported");
      return;
    }
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data: ")) continue;
        try {
          const payload = JSON.parse(line.slice(6)) as {
            type: string;
            content?: string;
            message_id?: number;
            message?: string;
          };
          if (payload.type === "token" && payload.content) handlers.onToken(payload.content);
          if (payload.type === "done" && payload.message_id) handlers.onDone(payload.message_id);
          if (payload.type === "error") handlers.onError(payload.message || "Stream error");
        } catch {
          // ignore malformed chunks
        }
      }
    }
  },

  async sendVoiceTurn(sessionId: number, audioBlob: Blob, showChineseHint?: boolean) {
    const form = new FormData();
    if (showChineseHint !== undefined) {
      form.append("show_chinese_hint", String(showChineseHint));
    }
    form.append("audio", audioBlob, "recording.webm");
    const res = await fetch(`${getApiBase()}/conversations/${sessionId}/turns/voice`, {
      method: "POST",
      headers: authHeaders(),
      body: form,
    });
    if (res.status === 401) {
      throw new ApiError("Not authenticated", 401);
    }
    if (!res.ok) throw new ApiError(await res.text(), res.status);
    const data = (await res.json()) as VoiceTurnResponse;
    return {
      ...data,
      audio_url: `${getApiBase()}${data.audio_url}`,
    };
  },
};
