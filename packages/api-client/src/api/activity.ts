import { request } from "../client";
import type {
  ActivityOverview,
  ActivityTimelineResponse,
  ConversationListResponse,
  ScenarioBrief,
} from "./types";

export const activityApi = {
  getActivityOverview: () => request<ActivityOverview>("/activity/overview"),

  getActivityTimeline: (skip = 0, limit = 30) =>
    request<ActivityTimelineResponse>(`/activity/timeline?skip=${skip}&limit=${limit}`),

  listScenariosPage: (skip = 0, limit = 20) =>
    request<{ items: ScenarioBrief[]; total: number }>(`/scenarios?skip=${skip}&limit=${limit}`),

  listConversationsPage: (page = 1, pageSize = 20) =>
    request<ConversationListResponse>(`/conversations?page=${page}&page_size=${pageSize}`),
};
