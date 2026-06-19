"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BookOpen, Home, Layers, Library } from "lucide-react";

import { cn } from "@/lib/utils";
import { prefetchNavTarget } from "@/lib/route-prefetch";
import { useQueryClient } from "@tanstack/react-query";

const tabs = [
  { href: "/", label: "首页", icon: Home },
  { href: "/activity", label: "学习", icon: Layers },
  { href: "/words", label: "词库", icon: BookOpen },
  { href: "/reference/phonetics", label: "参考", icon: Library },
] as const;

function isNavActive(pathname: string, href: string) {
  if (href === "/reference/phonetics") return pathname.startsWith("/reference");
  if (href === "/activity") {
    return (
      pathname.startsWith("/activity") ||
      pathname.startsWith("/scenarios") ||
      (pathname.startsWith("/chat") && !pathname.includes("/immersive"))
    );
  }
  return pathname === href;
}

export function MobileBottomNav() {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();

  const hidden =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/auth/") ||
    pathname.includes("/immersive");

  const prefetch = (href: string) => prefetchNavTarget(queryClient, router, href);

  if (hidden) return null;

  return (
    <nav className="mobile-bottom-nav fixed inset-x-0 bottom-0 z-50 flex items-stretch border-t border-surface-border/80 bg-white/95 shadow-[0_-4px_24px_rgba(15,23,42,0.06)] backdrop-blur md:hidden">
      {tabs.map(({ href, label, icon: Icon }) => {
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
    </nav>
  );
}
