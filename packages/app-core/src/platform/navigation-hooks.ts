"use client";

import { usePlatform } from "@sceneenglish/app-core/platform/context";

export function usePathname(): string {
  return usePlatform().navigation.usePathname();
}

export function useNavigate() {
  return usePlatform().navigation.navigate;
}
