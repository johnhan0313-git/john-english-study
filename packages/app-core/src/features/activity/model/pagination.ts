import type { ConversationListResponse, ScenarioBrief } from "@sceneenglish/api-client/types";

export const ACTIVITY_LIST_PAGE_SIZE = 20;

export interface PaginatedItems<T> {
  items: T[];
  total: number;
}

export function normalizePage<T>(page: PaginatedItems<T> | undefined | null): PaginatedItems<T> {
  return { items: page?.items ?? [], total: page?.total ?? 0 };
}

export function countLoadedPages<T>(pages: Array<PaginatedItems<T> | undefined | null>): number {
  return pages.reduce((sum, page) => sum + normalizePage(page).items.length, 0);
}

export type ScenarioListPage = PaginatedItems<ScenarioBrief>;
export type ConversationListPage = ConversationListResponse;

export const ACTIVITY_QUERY_KEYS = {
  overview: ["activity-overview"] as const,
  scenarios: ["activity", "scenarios", "list"] as const,
  conversations: ["activity", "conversations", "list"] as const,
  timeline: ["activity", "timeline"] as const,
};

export function scenariosNextPageParam(
  lastPage: ScenarioListPage | undefined | null,
  pages: Array<ScenarioListPage | undefined | null>,
) {
  const page = normalizePage(lastPage);
  const loaded = countLoadedPages(pages);
  return loaded < page.total ? loaded : undefined;
}

export function conversationsNextPageParam(
  lastPage: ConversationListPage | undefined | null,
  pages: Array<ConversationListPage | undefined | null>,
) {
  const page = normalizePage(lastPage);
  const loaded = countLoadedPages(pages);
  return loaded < page.total ? pages.length + 1 : undefined;
}

export function timelineNextPageParam(
  lastPage: PaginatedItems<unknown> | undefined | null,
  pages: Array<PaginatedItems<unknown> | undefined | null>,
) {
  const page = normalizePage(lastPage);
  const loaded = countLoadedPages(pages);
  return loaded < page.total ? loaded : undefined;
}
