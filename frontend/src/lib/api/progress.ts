import { authFetch, request } from "./client";
import type { ProgressOverview } from "./types";

export const progressApi = {
  getProgress: () => request<ProgressOverview>("/progress/overview"),

  getReviewWords: (limit = 20) => request<unknown[]>(`/progress/review?limit=${limit}`),

  evaluateWriting: (body: { prompt: string; content: string; target_words: string[] }) =>
    request<{
      score: number;
      grammar_feedback: string;
      vocabulary_feedback: string;
      used_target_words: string[];
      missing_target_words: string[];
      suggestions: string[];
    }>("/progress/writing/evaluate", { method: "POST", body: JSON.stringify(body) }),

  generateWritingSample: (body: {
    prompt: string;
    target_words: string[];
    level?: string;
    theme?: string;
    regenerate?: boolean;
  }) =>
    request<{ sample_en: string; sample_zh: string }>("/progress/writing/sample", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  evaluateSpeaking: async (expected: string, audioBlob: Blob) => {
    const form = new FormData();
    form.append("expected", expected);
    form.append("audio", audioBlob, "recording.webm");
    const res = await authFetch("/progress/speaking/evaluate", { method: "POST", body: form });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};
