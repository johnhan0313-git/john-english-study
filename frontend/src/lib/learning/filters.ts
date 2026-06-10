import type { ConversationBrief, ScenarioBrief } from "@/lib/api/types";

export interface ScenarioFilters {
  levels: string[];
  themes: string[];
  dailyOnly: boolean;
}

export interface ConversationFilters {
  levels: string[];
  statuses: string[];
}

export const EMPTY_SCENARIO_FILTERS: ScenarioFilters = {
  levels: [],
  themes: [],
  dailyOnly: false,
};

export const EMPTY_CONVERSATION_FILTERS: ConversationFilters = {
  levels: [],
  statuses: [],
};

export function uniqueThemes(scenarios: ScenarioBrief[]): string[] {
  return [...new Set(scenarios.map((s) => s.theme))].sort();
}

export function filterScenarios(items: ScenarioBrief[], filters: ScenarioFilters): ScenarioBrief[] {
  return items.filter((s) => {
    if (filters.levels.length && !filters.levels.includes(s.level)) return false;
    if (filters.themes.length && !filters.themes.includes(s.theme)) return false;
    if (filters.dailyOnly && !s.is_daily) return false;
    return true;
  });
}

export function filterConversations(items: ConversationBrief[], filters: ConversationFilters): ConversationBrief[] {
  return items.filter((c) => {
    if (filters.levels.length && !filters.levels.includes(c.level)) return false;
    if (filters.statuses.length && !filters.statuses.includes(c.status)) return false;
    return true;
  });
}

export function parseScenarioFiltersFromSearch(params: URLSearchParams): ScenarioFilters {
  return {
    levels: params.getAll("level"),
    themes: params.getAll("theme"),
    dailyOnly: params.get("daily") === "1",
  };
}

export function parseConversationFiltersFromSearch(params: URLSearchParams): ConversationFilters {
  return {
    levels: params.getAll("level"),
    statuses: params.getAll("status"),
  };
}

export function scenarioFiltersToSearch(filters: ScenarioFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const level of filters.levels) params.append("level", level);
  for (const theme of filters.themes) params.append("theme", theme);
  if (filters.dailyOnly) params.set("daily", "1");
  return params;
}

export function conversationFiltersToSearch(filters: ConversationFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const level of filters.levels) params.append("level", level);
  for (const status of filters.statuses) params.append("status", status);
  return params;
}
