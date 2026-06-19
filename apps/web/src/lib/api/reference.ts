import { API_BASE } from "@/lib/env";

import { request } from "./client";
import type { GrammarDetail, GrammarListResponse, PhoneticDetail, PhoneticListResponse } from "./types";

export const referenceApi = {
  getPhonetics: (params?: { category?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.search) qs.set("search", params.search);
    const q = qs.toString();
    return request<PhoneticListResponse>(`/reference/phonetics${q ? `?${q}` : ""}`);
  },

  getPhonetic: (id: number) => request<PhoneticDetail>(`/reference/phonetics/${id}`),

  getPhoneticAudioUrl: (id: number, opts?: { word?: string; preview?: boolean; kind?: "symbol" | "examples" }) => {
    const qs = new URLSearchParams();
    if (opts?.kind) qs.set("kind", opts.kind);
    if (opts?.word) qs.set("word", opts.word);
    if (opts?.preview) qs.set("preview", "true");
    const q = qs.toString();
    return `${API_BASE}/reference/phonetics/${id}/audio${q ? `?${q}` : ""}`;
  },

  getGrammar: (params?: { category?: string; level?: string; search?: string }) => {
    const qs = new URLSearchParams();
    if (params?.category) qs.set("category", params.category);
    if (params?.level) qs.set("level", params.level);
    if (params?.search) qs.set("search", params.search);
    const q = qs.toString();
    return request<GrammarListResponse>(`/reference/grammar${q ? `?${q}` : ""}`);
  },

  getGrammarPoint: (slug: string) => request<GrammarDetail>(`/reference/grammar/${slug}`),
};
