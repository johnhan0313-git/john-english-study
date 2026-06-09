import type { QueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { API_BASE } from "@/lib/env";
import { getAccessToken } from "@/lib/auth/token";

export const NAV_ROUTES = [
  "/",
  "/words",
  "/scenarios",
  "/chat",
  "/chat/new",
  "/generate",
  "/reference/phonetics",
  "/reference/grammar",
  "/progress",
  "/settings",
] as const;

type AppRouter = { prefetch: (href: string) => void };

function isAuthenticated() {
  return !!getAccessToken();
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
    case "/scenarios":
      if (authed) {
        void qc.prefetchQuery({
          queryKey: ["scenarios"],
          queryFn: () => api.listScenarios(),
        });
      }
      break;
    case "/chat":
    case "/chat/new":
      if (authed) {
        void qc.prefetchQuery({
          queryKey: ["conversations"],
          queryFn: () => api.listConversations(),
        });
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
    case "/settings":
      void qc.prefetchQuery({
        queryKey: ["ai-config"],
        queryFn: async () => {
          const res = await fetch(`${API_BASE}/config/ai`);
          if (!res.ok) throw new Error("Failed to load AI config");
          return res.json();
        },
      });
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
  if (href.startsWith("/chat")) {
    prefetchRouteData(qc, "/chat");
  }
  if (href.startsWith("/reference")) {
    prefetchRouteData(qc, "/reference/phonetics");
    prefetchRouteData(qc, "/reference/grammar");
  }
}
