"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  BookOpen,
  Home,
  Layers,
  Library,
  LineChart,
  MessageCircle,
  MoreHorizontal,
  Sparkles,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { prefetchNavTarget } from "@/lib/route-prefetch";
import { useQueryClient } from "@tanstack/react-query";

const primaryTabs = [
  { href: "/", label: "首页", icon: Home },
  { href: "/words", label: "词库", icon: BookOpen },
  { href: "/chat", label: "对话", icon: MessageCircle },
  { href: "/scenarios", label: "场景", icon: Layers },
] as const;

const moreLinks = [
  { href: "/generate", label: "生成", icon: Sparkles },
  { href: "/reference/phonetics", label: "参考", icon: Library },
  { href: "/progress", label: "进度", icon: LineChart },
] as const;

function isNavActive(pathname: string, href: string) {
  if (href === "/reference/phonetics") return pathname.startsWith("/reference");
  if (href === "/chat") return pathname.startsWith("/chat");
  return pathname === href;
}

function isMoreActive(pathname: string) {
  return moreLinks.some((item) => isNavActive(pathname, item.href));
}

export function MobileBottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [moreOpen, setMoreOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const hidden =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/auth/") ||
    pathname.includes("/immersive");

  useEffect(() => {
    setMoreOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!moreOpen) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setMoreOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [moreOpen]);

  const prefetch = (href: string) => prefetchNavTarget(queryClient, router, href);

  if (hidden) return null;

  return (
    <div ref={rootRef} className="fixed inset-x-0 bottom-0 z-50 md:hidden">
      {moreOpen && (
        <div className="absolute inset-x-3 bottom-[calc(100%+0.5rem)] rounded-2xl border border-surface-border/80 bg-white p-2 shadow-lg">
          {moreLinks.map(({ href, label, icon: Icon }) => {
            const active = isNavActive(pathname, href);
            return (
              <Link
                key={href}
                href={href}
                prefetch
                onClick={() => setMoreOpen(false)}
                onMouseEnter={() => prefetch(href)}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                  active ? "bg-brand-50 text-brand-700" : "text-slate-700 hover:bg-slate-50",
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            );
          })}
        </div>
      )}

      <nav className="mobile-bottom-nav flex items-stretch border-t border-surface-border/80 bg-white/95 shadow-[0_-4px_24px_rgba(15,23,42,0.06)] backdrop-blur">
        {primaryTabs.map(({ href, label, icon: Icon }) => {
          const active = isNavActive(pathname, href);
          return (
            <Link
              key={href}
              href={href}
              prefetch
              onMouseEnter={() => prefetch(href)}
              className={cn(
                "flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
                active ? "text-brand-600" : "text-slate-500",
              )}
            >
              <Icon className={cn("h-5 w-5", active && "stroke-[2.5px]")} />
              {label}
            </Link>
          );
        })}

        <button
          type="button"
          onClick={() => setMoreOpen((v) => !v)}
          className={cn(
            "flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium transition-colors",
            isMoreActive(pathname) || moreOpen ? "text-brand-600" : "text-slate-500",
          )}
        >
          <MoreHorizontal className={cn("h-5 w-5", (isMoreActive(pathname) || moreOpen) && "stroke-[2.5px]")} />
          更多
        </button>
      </nav>
    </div>
  );
}
