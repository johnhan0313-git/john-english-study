"use client";

import type { ReactNode } from "react";

import { usePlatformLink } from "../platform/context";

export function PlatformLink({
  href,
  className,
  children,
  onClick,
  onMouseEnter,
  onFocus,
}: {
  href: string;
  className?: string;
  children: ReactNode;
  onClick?: () => void;
  onMouseEnter?: () => void;
  onFocus?: () => void;
  prefetch?: boolean;
  role?: string;
}) {
  const Link = usePlatformLink();
  return (
    <Link href={href} className={className} onClick={onClick}>
      {children}
    </Link>
  );
}
