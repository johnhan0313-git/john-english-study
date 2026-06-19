"use client";

import Link from "next/link";
import {
  useParams as useNextParams,
  usePathname as useNextPathname,
  useRouter,
  useSearchParams as useNextSearchParams,
} from "next/navigation";
import { useMemo, type ReactNode } from "react";

import { AppProviders } from "@sceneenglish/app-core";
import { createBasePlatform } from "@sceneenglish/app-core/platform/browser";
import type { PlatformLinkProps, PlatformNavigation } from "@sceneenglish/app-core/platform/types";

function NextLink({ href, className, children, onClick }: PlatformLinkProps) {
  return (
    <Link href={href} className={className} onClick={onClick}>
      {children}
    </Link>
  );
}

export function WebPlatformProviders({
  apiBase,
  children,
}: {
  apiBase: string;
  children: ReactNode;
}) {
  const router = useRouter();

  const navigation = useMemo<PlatformNavigation>(
    () => ({
      navigate: (path, opts) => {
        if (opts?.replace) router.replace(path, { scroll: opts.scroll ?? true });
        else router.push(path, { scroll: opts?.scroll ?? true });
      },
      useParams: useNextParams,
      useSearchParams: useNextSearchParams,
      usePathname: useNextPathname,
      Link: NextLink,
      prefetch: (path) => router.prefetch(path),
    }),
    [router],
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
