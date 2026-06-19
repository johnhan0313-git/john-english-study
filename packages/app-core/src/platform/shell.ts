import { createBasePlatform } from "./browser";
import type { PlatformNavigation } from "./types";

/** Shell (Vite SPA) platform factory — navigation supplied by react-router adapter in apps/shell */
export function createShellPlatform(navigation: PlatformNavigation, apiBase: string) {
  return createBasePlatform(navigation, { apiBase, runtime: "web" });
}
