import type { QueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { API_BASE } from "@/lib/env";
import { getDeviceId } from "@/lib/utils";

export const NAV_ROUTES = [
  "/",
  "/words",
  "/scenarios",
  "/generate",
  "/reference/phonetics",
  "/reference/grammar",
  "/progress",
  "/settings",
] as const;

type AppRouter = { prefetch: (href: string) => void };

export function prefetchRouteData(qc: QueryClient, href: string) {
  const deviceId = getDeviceId();

  switch (href) {
    case "/":
      void qc.prefetchQuery({
        queryKey: ["progress", deviceId],
        queryFn: () => api.getProgress(deviceId),
      });
      void qc.prefetchQuery({
        queryKey: ["daily", deviceId],
        queryFn: () => api.getDailyScenarios(deviceId),
      });
      break;
    case "/words":
      void qc.prefetchQuery({
        queryKey: ["groups"],
        queryFn: () => api.getWordGroups(),
      });
      void qc.prefetchQuery({
        queryKey: ["words", 1, "", "", "", deviceId],
        queryFn: () => api.getWords({ page: 1, page_size: 30, device_id: deviceId }),
      });
      break;
    case "/scenarios":
      void qc.prefetchQuery({
        queryKey: ["scenarios", deviceId],
        queryFn: () => api.listScenarios(deviceId),
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
      void qc.prefetchQuery({
        queryKey: ["progress", deviceId],
        queryFn: () => api.getProgress(deviceId),
      });
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
  if (href.startsWith("/reference")) {
    prefetchRouteData(qc, "/reference/phonetics");
    prefetchRouteData(qc, "/reference/grammar");
  }
}
