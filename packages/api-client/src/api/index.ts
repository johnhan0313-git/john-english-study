import { activityApi } from "./activity";
import { request } from "../client";
import { conversationsApi } from "./conversations";
import { progressApi } from "./progress";
import { referenceApi } from "./reference";
import { scenariosApi } from "./scenarios";
import { wordsApi } from "./words";

export { ApiError, request, API_BASE } from "../client";
export * from "./types";

export const api = {
  health: () => request<{ status: string; app: string }>("/health"),
  ...wordsApi,
  ...scenariosApi,
  ...progressApi,
  ...referenceApi,
  ...conversationsApi,
  ...activityApi,
};
