"use client";

import {
  Link as RouterLink,
  useLocation,
  useNavigate as useRouterNavigate,
  useParams as useRouterParams,
  useSearchParams as useRouterSearchParams,
} from "react-router-dom";
import { useMemo, type ReactNode } from "react";

import { AppProviders } from "@sceneenglish/app-core/index";
import { createBasePlatform } from "@sceneenglish/app-core/platform/browser";
import type { PlatformLinkProps, PlatformNavigation } from "@sceneenglish/app-core/platform/types";

function ShellLink({ href, className, children, onClick }: PlatformLinkProps) {
  return (
    <RouterLink to={href} className={className} onClick={onClick}>
      {children}
    </RouterLink>
  );
}

function useShellParams<T extends Record<string, string>>(): T {
  return useRouterParams() as T;
}

function useShellSearchParams(): URLSearchParams {
  const [params] = useRouterSearchParams();
  return params;
}

function useShellPathname(): string {
  return useLocation().pathname;
}

export function ShellPlatformProviders({
  apiBase,
  children,
}: {
  apiBase: string;
  children: ReactNode;
}) {
  const routerNavigate = useRouterNavigate();

  const navigation = useMemo<PlatformNavigation>(
    () => ({
      navigate: (path, opts) => {
        if (opts?.replace) routerNavigate(path, { replace: true });
        else routerNavigate(path);
      },
      useParams: useShellParams,
      useSearchParams: useShellSearchParams,
      usePathname: useShellPathname,
      Link: ShellLink,
    }),
    [routerNavigate],
  );

  const platform = useMemo(
    () =>
      createBasePlatform(navigation, {
        apiBase,
        runtime: "web",
        onUnauthorized: () => {
          window.dispatchEvent(new CustomEvent("auth:unauthorized"));
        },
      }),
    [navigation, apiBase],
  );

  return <AppProviders platform={platform}>{children}</AppProviders>;
}
