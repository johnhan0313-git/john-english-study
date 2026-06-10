"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { BookOpen, Home, Layers, Library, LineChart, MessageCircle, Sparkles, GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";
import { AuthNavActions } from "@/components/auth/user-menu";
import { prefetchAllRoutes, prefetchNavTarget } from "@/lib/route-prefetch";

const nav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/words", label: "词库", icon: BookOpen },
  { href: "/scenarios", label: "场景", icon: Layers },
  { href: "/chat", label: "对话", icon: MessageCircle },
  { href: "/generate", label: "生成", icon: Sparkles },
  { href: "/reference/phonetics", label: "参考", icon: Library },
  { href: "/progress", label: "进度", icon: LineChart },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();

  useEffect(() => {
    prefetchAllRoutes(queryClient, router);
  }, [queryClient, router]);

  return (
    <header className="site-header">
      <div className="mx-auto flex h-full max-w-6xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link href="/" className="group flex min-w-0 shrink items-center gap-2 sm:gap-2.5" prefetch>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-hero-gradient text-white shadow-md transition-transform group-hover:scale-105">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div className="min-w-0 flex flex-col leading-none">
            <span className="truncate font-display text-sm font-bold text-slate-900 sm:text-base">SceneEnglish</span>
            <span className="hidden text-[10px] font-semibold uppercase tracking-wider text-brand-600 sm:block">
              CET-4 / CET-6
            </span>
          </div>
        </Link>

        <div className="flex min-w-0 items-center gap-2">
          <nav className="hidden items-center gap-0.5 overflow-x-auto rounded-2xl border border-surface-border/80 bg-white p-1 shadow-sm md:flex [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {nav.map(({ href, label, icon: Icon }) => {
              const active = href === "/reference/phonetics"
                ? pathname.startsWith("/reference")
                : href === "/chat"
                  ? pathname.startsWith("/chat")
                  : pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  prefetch
                  onMouseEnter={() => prefetchNavTarget(queryClient, router, href)}
                  onFocus={() => prefetchNavTarget(queryClient, router, href)}
                  className={cn(
                    "flex shrink-0 items-center gap-1.5 rounded-xl px-2.5 py-2 text-sm font-medium transition-colors lg:px-3",
                    active
                      ? "bg-hero-gradient text-white shadow-md"
                      : "text-slate-600 hover:bg-brand-50 hover:text-brand-700",
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  <span className="hidden lg:inline">{label}</span>
                </Link>
              );
            })}
          </nav>
          <AuthNavActions />
        </div>
      </div>
    </header>
  );
}
