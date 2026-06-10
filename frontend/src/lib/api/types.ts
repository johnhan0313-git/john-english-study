export interface WordBrief {
  id: number;
  lemma: string;
  phonetic: string | null;
  level: string;
  pos: string | null;
  definitions: string[];
  familiarity: number | null;
  exam_levels?: string[];
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
  summary_preview?: string | null;
  is_completed?: boolean;
  best_score?: number | null;
  conversation_count?: number;
  exercise_count?: number;
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
  scenario_id?: number | null;
  ended_at?: string | null;
}

export interface ConversationDetail extends ConversationBrief {
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

export interface HeatmapDay {
  date: string;
  count: number;
}

export interface ActivityOverview {
  scenario_total: number;
  scenario_this_week: number;
  conversation_total: number;
  conversation_active: number;
  theme_counts: Record<string, number>;
  heatmap: HeatmapDay[];
  continue: {
    active_conversations: ConversationBrief[];
    incomplete_scenarios: ScenarioBrief[];
  };
}

export type ActivityTimelineItem =
  | { type: "scenario_created"; at: string; scenario: ScenarioBrief }
  | { type: "scenario_completed"; at: string; scenario: ScenarioBrief; score: number }
  | { type: "conversation_started"; at: string; conversation: ConversationBrief }
  | { type: "conversation_ended"; at: string; conversation: ConversationBrief };

export interface ActivityTimelineResponse {
  items: ActivityTimelineItem[];
  total: number;
}
