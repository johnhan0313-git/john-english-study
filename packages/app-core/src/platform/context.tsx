"use client";

import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";
import { configureApiClient } from "@sceneenglish/api-client";

import {
  getAccessTokenSync,
  loadAccessToken,
  persistAccessToken,
  setAccessTokenCache,
  ACCESS_TOKEN_KEY,
} from "../features/auth";
import type { PlatformServices } from "./types";

const PlatformContext = createContext<PlatformServices | null>(null);

function bindApiClient(platform: PlatformServices): void {
  configureApiClient({
    getBaseUrl: () => platform.getApiBase(),
    getToken: () => getAccessTokenSync(),
    onUnauthorized: () => {
      setAccessTokenCache(null);
      void platform.storage.remove(ACCESS_TOKEN_KEY);
      platform.onUnauthorized?.();
    },
    getOrigin: () =>
      typeof window !== "undefined" ? window.location.origin : "http://localhost",
  });
}

export function PlatformProvider({
  platform,
  children,
}: {
  platform: PlatformServices;
  children: ReactNode;
}) {
  useEffect(() => {
    bindApiClient(platform);
    void loadAccessToken((key) => platform.storage.get(key));
  }, [platform]);

  const value = useMemo(() => platform, [platform]);

  return <PlatformContext.Provider value={value}>{children}</PlatformContext.Provider>;
}

export function usePlatform(): PlatformServices {
  const ctx = useContext(PlatformContext);
  if (!ctx) {
    throw new Error("usePlatform must be used within PlatformProvider");
  }
  return ctx;
}

export function useNavigate() {
  return usePlatform().navigation.navigate;
}

export function useParams<T extends Record<string, string> = Record<string, string>>(): T {
  const useParamsHook = usePlatform().navigation.useParams;
  return useParamsHook<T>();
}

export function useSearchParams(): URLSearchParams {
  const useSearchParamsHook = usePlatform().navigation.useSearchParams;
  return useSearchParamsHook();
}

export function usePlatformLink() {
  return usePlatform().navigation.Link;
}

export async function setAccessToken(platform: PlatformServices, token: string): Promise<void> {
  await persistAccessToken(platform.storage, token);
}

export async function clearAccessToken(platform: PlatformServices): Promise<void> {
  await persistAccessToken(platform.storage, null);
}

export { getAccessTokenSync as getAccessToken };
