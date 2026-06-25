import { getApiBase, request } from "../client";
import type { WordGroup, WordListResponse } from "./types";

export const wordsApi = {
  getWords: (params: Record<string, string | number>) => {
    const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
    return request<WordListResponse>(`/words?${qs}`);
  },

  getWordStats: () =>
    request<{ total: number; learned: number; mastered: number; due_review: number; mastery_rate: number }>(
      "/words/stats",
    ),

  getWordGroups: () => request<WordGroup[]>("/words/groups"),

  getWordLetters: (params: Record<string, string>) => {
    const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v));
    return request<{ letters: string[] }>(`/words/letters?${qs}`);
  },

  getWordAudioUrl: (wordId: number) => `${getApiBase()}/words/${wordId}/audio`,
};
