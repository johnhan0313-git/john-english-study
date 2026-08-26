"use client";

import { usePlatform } from "./context";

export function usePathname(): string {
  return usePlatform().navigation.usePathname();
}

export function useNavigate() {
  return usePlatform().navigation.navigate;
}
