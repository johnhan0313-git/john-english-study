import type { ConversationBrief, ScenarioBrief } from "@sceneenglish/api-client/types";

export type ScenarioKind = "daily" | "narrative" | "dialogue";

export interface ScenarioFilters {
  levels: string[];
  themes: string[];
  /** null = 全部 */
  scenarioKind: ScenarioKind | null;
}

export interface ConversationFilters {
  levels: string[];
  statuses: string[];
}

export const EMPTY_SCENARIO_FILTERS: ScenarioFilters = {
  levels: [],
  themes: [],
  scenarioKind: null,
};

export const EMPTY_CONVERSATION_FILTERS: ConversationFilters = {
  levels: [],
  statuses: [],
};

export function filterScenarios(items: ScenarioBrief[], filters: ScenarioFilters): ScenarioBrief[] {
  const levels = filters.levels ?? [];
  const themes = filters.themes ?? [];

  return items.filter((s) => {
    if (levels.length && !levels.includes(s.level)) return false;
    if (themes.length && !themes.includes(s.theme)) return false;
    if (filters.scenarioKind === "daily" && !s.is_daily) return false;
    if (filters.scenarioKind === "narrative" && s.scenario_type !== "narrative") return false;
    if (filters.scenarioKind === "dialogue" && s.scenario_type !== "dialogue") return false;
    return true;
  });
}

export function filterConversations(items: ConversationBrief[], filters: ConversationFilters): ConversationBrief[] {
  const levels = filters.levels ?? [];
  const statuses = filters.statuses ?? [];
  return items.filter((c) => {
    if (levels.length && !levels.includes(c.level)) return false;
    if (statuses.length && !statuses.includes(c.status)) return false;
    return true;
  });
}

export function parseScenarioFiltersFromSearch(params: URLSearchParams): ScenarioFilters {
  const kindParam = params.get("kind");
  let scenarioKind: ScenarioKind | null = null;
  if (kindParam === "daily" || kindParam === "narrative" || kindParam === "dialogue") {
    scenarioKind = kindParam;
  } else if (params.get("daily") === "1") {
    scenarioKind = "daily";
  }

  return {
    levels: params.getAll("level"),
    themes: params.getAll("theme"),
    scenarioKind,
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
  if (filters.scenarioKind) params.set("kind", filters.scenarioKind);
  return params;
}

export function conversationFiltersToSearch(filters: ConversationFilters): URLSearchParams {
  const params = new URLSearchParams();
  for (const level of filters.levels) params.append("level", level);
  for (const status of filters.statuses) params.append("status", status);
  return params;
}
