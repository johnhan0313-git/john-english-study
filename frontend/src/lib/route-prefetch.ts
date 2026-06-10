import type { QueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth/token";
import {
  ACTIVITY_LIST_PAGE_SIZE,
  ACTIVITY_QUERY_KEYS,
  conversationsNextPageParam,
  normalizePage,
  scenariosNextPageParam,
} from "@/lib/learning/pagination";

export const NAV_ROUTES = [
  "/",
  "/words",
  "/activity",
  "/chat/new",
  "/generate",
  "/reference/phonetics",
  "/reference/grammar",
  "/progress",
  "/profile",
] as const;

type AppRouter = { prefetch: (href: string) => void };

function isAuthenticated() {
  return !!getAccessToken();
}

function prefetchActivity(qc: QueryClient) {
  void qc.prefetchQuery({
    queryKey: ACTIVITY_QUERY_KEYS.overview,
    queryFn: () => api.getActivityOverview(),
  });
  void qc.prefetchInfiniteQuery({
    queryKey: ACTIVITY_QUERY_KEYS.scenarios,
    queryFn: async ({ pageParam = 0 }) =>
      normalizePage(await api.listScenariosPage(pageParam, ACTIVITY_LIST_PAGE_SIZE)),
    initialPageParam: 0,
    getNextPageParam: scenariosNextPageParam,
  });
  void qc.prefetchInfiniteQuery({
    queryKey: ACTIVITY_QUERY_KEYS.conversations,
    queryFn: async ({ pageParam = 1 }) =>
      normalizePage(await api.listConversationsPage(pageParam, ACTIVITY_LIST_PAGE_SIZE)),
    initialPageParam: 1,
    getNextPageParam: conversationsNextPageParam,
  });
}

export function prefetchRouteData(qc: QueryClient, href: string) {
  const authed = isAuthenticated();

  switch (href) {
    case "/":
      if (authed) {
        void qc.prefetchQuery({
          queryKey: ["progress"],
          queryFn: () => api.getProgress(),
        });
        void qc.prefetchQuery({
          queryKey: ["daily"],
          queryFn: () => api.getDailyScenarios(),
        });
      }
      break;
    case "/words":
      void qc.prefetchQuery({
        queryKey: ["groups"],
        queryFn: () => api.getWordGroups(),
      });
      void qc.prefetchQuery({
        queryKey: ["words", 1, "", "", ""],
        queryFn: () => api.getWords({ page: 1, page_size: 30 }),
      });
      break;
    case "/activity":
      if (authed) {
        prefetchActivity(qc);
      }
      break;
    case "/chat/new":
      if (authed) {
        prefetchActivity(qc);
      }
      void qc.prefetchQuery({
        queryKey: ["groups"],
        queryFn: () => api.getWordGroups(),
      });
      break;
    case "/generate":
      void qc.prefetchQuery({
        queryKey: ["groups"],
        queryFn: () => api.getWordGroups(),
      });
      break;
    case "/reference/phonetics":
      void qc.prefetchQuery({
        queryKey: ["phonetics", "", ""],
        queryFn: () => api.getPhonetics(),
      });
      break;
    case "/reference/grammar":
      void qc.prefetchQuery({
        queryKey: ["grammar", "", ""],
        queryFn: () => api.getGrammar(),
      });
      break;
    case "/progress":
      if (authed) {
        void qc.prefetchQuery({
          queryKey: ["progress"],
          queryFn: () => api.getProgress(),
        });
      }
      break;
    default:
      break;
  }
}

export function prefetchAllRoutes(qc: QueryClient, router: AppRouter) {
  for (const href of NAV_ROUTES) {
    router.prefetch(href);
  }

  const prefetchData = () => {
    for (const href of NAV_ROUTES) {
      prefetchRouteData(qc, href);
    }
  };

  if (typeof requestIdleCallback !== "undefined") {
    requestIdleCallback(prefetchData, { timeout: 2000 });
  } else {
    window.setTimeout(prefetchData, 300);
  }
}

export function prefetchNavTarget(qc: QueryClient, router: AppRouter, href: string) {
  router.prefetch(href);
  prefetchRouteData(qc, href);
  if (href.startsWith("/chat") || href.startsWith("/activity") || href.startsWith("/scenarios")) {
    prefetchRouteData(qc, "/activity");
  }
  if (href.startsWith("/reference")) {
    prefetchRouteData(qc, "/reference/phonetics");
    prefetchRouteData(qc, "/reference/grammar");
  }
}
