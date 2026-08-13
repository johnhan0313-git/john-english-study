"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { BookOpen, Home, Layers, Library } from "lucide-react";
import { cn } from "@/lib/utils";
import { AuthNavActions } from "@/components/auth/user-menu";
import { prefetchAllRoutes, prefetchNavTarget } from "@/lib/route-prefetch";
import { AppLogo } from "@johnhan0313-git/shared/brand";

const nav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/activity", label: "学习", icon: Layers },
  { href: "/words", label: "词库", icon: BookOpen },
  { href: "/reference/phonetics", label: "参考", icon: Library },
];

function isLearningActive(pathname: string) {
  return (
    pathname.startsWith("/activity") ||
    pathname.startsWith("/scenarios") ||
    (pathname.startsWith("/chat") && !pathname.includes("/immersive"))
  );
}

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
          <AppLogo
            appId="english"
            size={36}
            className="h-9 w-9 shrink-0 rounded-lg transition-transform group-hover:scale-[1.03]"
            alt="Scene English"
          />
          <div className="min-w-0 flex flex-col leading-none">
            <span className="truncate font-display text-sm font-bold text-slate-950 sm:text-base">Scene English</span>
            <span className="hidden text-[10px] font-medium text-slate-500 sm:block">
              场景化英语学习
            </span>
          </div>
        </Link>

        <div className="flex min-w-0 items-center gap-2">
          <nav className="hidden items-center gap-1 overflow-x-auto md:flex [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
            {nav.map(({ href, label, icon: Icon }) => {
              const active =
                href === "/reference/phonetics"
                  ? pathname.startsWith("/reference")
                  : href === "/activity"
                    ? isLearningActive(pathname)
                    : pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  prefetch
                  onMouseEnter={() => prefetchNavTarget(queryClient, router, href)}
                  onFocus={() => prefetchNavTarget(queryClient, router, href)}
                  className={cn(
                    "flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors lg:px-3",
                    active
                      ? "bg-brand-50 text-brand-800"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
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
