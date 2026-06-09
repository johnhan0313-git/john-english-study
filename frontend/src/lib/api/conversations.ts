import { API_BASE } from "@/lib/env";

import { ApiError, request } from "./client";
import type { ConversationDetail, ConversationListResponse, ConversationSummary, VoiceTurnResponse } from "./types";

export const conversationsApi = {
  createConversation: (body: {
    device_id: string;
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

  listConversations: (deviceId: string, page = 1) =>
    request<ConversationListResponse>(`/conversations?device_id=${deviceId}&page=${page}`),

  getConversation: (id: number, deviceId: string) =>
    request<ConversationDetail>(`/conversations/${id}?device_id=${deviceId}`),

  endConversation: (id: number, deviceId: string) =>
    request<ConversationSummary>(`/conversations/${id}/end`, {
      method: "POST",
      body: JSON.stringify({ device_id: deviceId }),
    }),

  getConversationMessageAudioUrl: (sessionId: number, messageId: number, deviceId: string) =>
    `${API_BASE}/conversations/${sessionId}/messages/${messageId}/audio?device_id=${deviceId}`,

  async streamConversationMessage(
    sessionId: number,
    deviceId: string,
    content: string,
    showChineseHint: boolean,
    handlers: {
      onToken: (token: string) => void;
      onDone: (messageId: number) => void;
      onError: (message: string) => void;
    },
  ) {
    const res = await fetch(
      `${API_BASE}/conversations/${sessionId}/messages/stream?device_id=${encodeURIComponent(deviceId)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, show_chinese_hint: showChineseHint }),
      },
    );
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

  async sendVoiceTurn(sessionId: number, deviceId: string, audioBlob: Blob, showChineseHint = true) {
    const form = new FormData();
    form.append("device_id", deviceId);
    form.append("show_chinese_hint", String(showChineseHint));
    form.append("audio", audioBlob, "recording.webm");
    const res = await fetch(`${API_BASE}/conversations/${sessionId}/turns/voice`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new ApiError(await res.text(), res.status);
    const data = (await res.json()) as VoiceTurnResponse;
    return {
      ...data,
      audio_url: `${API_BASE}${data.audio_url}`,
    };
  },
};
