import { API_BASE } from "@/lib/env";

import { request } from "./client";
import type { ProgressOverview } from "./types";
import { ApiError } from "./client";

export const progressApi = {
  getProgress: (deviceId: string) =>
    request<ProgressOverview>(`/progress/overview?device_id=${deviceId}`),

  evaluateSpeaking: async (expected: string, audioBlob: Blob) => {
    const form = new FormData();
    form.append("expected", expected);
    form.append("audio", audioBlob, "recording.webm");
    const res = await fetch(`${API_BASE}/progress/speaking/evaluate`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) throw new ApiError(await res.text(), res.status);
    return res.json() as Promise<{
      transcript: string;
      expected: string;
      match_rate: number;
      missing_words: string[];
      feedback: string;
    }>;
  },

  evaluateWriting: (body: { prompt: string; content: string; target_words: string[]; device_id: string }) =>
    request<{
      score: number;
      grammar_feedback: string;
      vocabulary_feedback: string;
      used_target_words: string[];
      missing_target_words: string[];
      suggestions: string[];
    }>("/progress/writing/evaluate", { method: "POST", body: JSON.stringify(body) }),
};
