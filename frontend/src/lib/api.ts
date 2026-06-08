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

export interface ConversationMessage {
  id: number;
  role: string;
  content: string;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface ConversationBrief {
  id: number;
  title: string;
  theme: string;
  level: string;
  role_ai: string;
  role_user: string;
  mode: string;
  status: string;
  turn_count: number;
  target_words: string[];
  words_used: string[];
  last_message: string | null;
  created_at: string;
}

export interface ConversationDetail extends ConversationBrief {
  scenario_id: number | null;
  scene_brief: Record<string, string>;
  summary: string | null;
  messages: ConversationMessage[];
}

export interface ConversationListResponse {
  items: ConversationBrief[];
  total: number;
}

export interface ConversationSummary {
  session_id: number;
  summary: string;
  words_used: string[];
  missing_words: string[];
  grammar_feedback: string;
  vocabulary_feedback: string;
  suggestions: string[];
}

export interface VoiceTurnResponse {
  user_message_id: number;
  assistant_message_id: number;
  transcript: string;
  content: string;
  audio_url: string;
  used_words: string[];
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
      const text = await res.text();
      handlers.onError(text || res.statusText);
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
