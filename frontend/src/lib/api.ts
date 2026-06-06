import { API_BASE } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiError(text || res.statusText, res.status);
  }
  if (res.headers.get("content-type")?.includes("application/json")) {
    return res.json();
  }
  return res as unknown as T;
}

export interface WordBrief {
  id: number;
  lemma: string;
  phonetic: string | null;
  level: string;
  pos: string | null;
  definitions: string[];
  familiarity: number | null;
}

export interface WordListResponse {
  items: WordBrief[];
  total: number;
  page: number;
  page_size: number;
}

export interface WordGroup {
  id: number;
  slug: string;
  name_zh: string;
  name_en: string;
  description: string | null;
  word_count: number;
}

export interface ScenarioBrief {
  id: number;
  title: string;
  theme: string;
  level: string;
  scenario_type: string;
  is_daily: boolean;
  daily_kind: string | null;
  word_count: number;
  created_at: string;
}

export interface ScenarioDetail extends ScenarioBrief {
  content: {
    passage: string;
    summary_zh: string;
    fun_fact: string | null;
    word_usage: { word: string; sentence: string; meaning_zh?: string }[];
  };
  dialogue: { speaker: string; text: string }[];
  words: string[];
  has_audio: boolean;
  exercise_count: number;
}

export interface Exercise {
  id: number;
  scenario_id: number;
  type: string;
  payload: {
    question: string;
    options?: { label: string; text: string }[];
    passage_with_blanks?: string;
    blanks?: { index: number; hint?: string; answer: string; accept?: string[] }[];
    explanation?: string;
  };
  sort_order: number;
}

export interface ProgressOverview {
  total_words: number;
  learned_words: number;
  mastered_words: number;
  due_review: number;
  mastery_rate: number;
  scenarios_completed: number;
  current_streak: number;
  longest_streak: number;
  exercises_completed: number;
}

export interface PhoneticExample {
  word: string;
  ipa: string;
  meaning_zh: string;
}

export interface PhoneticBrief {
  id: number;
  symbol: string;
  category: string;
  subcategory?: string | null;
  name_zh: string;
  name_en: string;
  preview_word?: string | null;
}

export interface PhoneticDetail extends PhoneticBrief {
  description?: string | null;
  examples: PhoneticExample[];
  sound_cue?: string | null;
}

export interface PhoneticCategoryGroup {
  category: string;
  category_zh: string;
  items: PhoneticBrief[];
  count: number;
}

export interface PhoneticListResponse {
  items: PhoneticBrief[];
  groups: PhoneticCategoryGroup[];
  total: number;
}

export interface GrammarExample {
  en: string;
  zh: string;
  note?: string | null;
}

export interface GrammarBrief {
  id: number;
  slug: string;
  category: string;
  title: string;
  level: string;
  summary: string;
}

export interface GrammarDetail extends GrammarBrief {
  structure?: string | null;
  rules: string[];
  examples: GrammarExample[];
  tips?: string | null;
}

export interface GrammarCategoryGroup {
  category: string;
  category_zh: string;
  items: GrammarBrief[];
  count: number;
}

export interface GrammarListResponse {
  items: GrammarBrief[];
  groups: GrammarCategoryGroup[];
  total: number;
}

export const api = {
  health: () => request<{ status: string; app: string }>("/health"),

  getWords: (params: Record<string, string | number>) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)]),
    );
    return request<WordListResponse>(`/words?${qs}`);
  },

  getWordStats: (deviceId: string) =>
    request<{ total: number; learned: number; mastered: number; due_review: number; mastery_rate: number }>(
      `/words/stats?device_id=${deviceId}`,
    ),

  getWordGroups: () => request<WordGroup[]>("/words/groups"),

  generateScenario: (body: {
    theme?: string;
    level: string;
    word_ids?: number[];
    scenario_type: string;
    device_id: string;
    word_count: number;
  }) =>
    request<ScenarioDetail>("/scenarios/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getDailyScenarios: (deviceId: string) =>
    request<{ date: string; items: ScenarioBrief[]; generated: boolean }>(
      `/scenarios/daily?device_id=${deviceId}`,
    ),

  listScenarios: (deviceId: string) =>
    request<{ items: ScenarioBrief[]; total: number }>(
      `/scenarios?device_id=${deviceId}`,
    ),

  getScenario: (id: number) => request<ScenarioDetail>(`/scenarios/${id}`),

  getScenarioAudioUrl: (id: number) => `${API_BASE}/scenarios/${id}/audio`,

  getExercises: (scenarioId: number) =>
    request<Exercise[]>(`/exercises/scenario/${scenarioId}`),

  submitExercise: (exerciseId: number, answer: string | string[], deviceId: string) =>
    request<{ correct: boolean; correct_answer: string | string[]; explanation?: string }>(
      `/exercises/${exerciseId}/submit`,
      { method: "POST", body: JSON.stringify({ answer, device_id: deviceId }) },
    ),

  submitBatch: (scenarioId: number, answers: Record<number, string | string[]>, deviceId: string) =>
    request<{ score: number; total: number; correct: number; results: { correct: boolean }[] }>(
      `/exercises/scenario/${scenarioId}/submit`,
      { method: "POST", body: JSON.stringify({ answers, device_id: deviceId }) },
    ),

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
