"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Home, Layers, LineChart, Settings, Sparkles, GraduationCap } from "lucide-react";
import { cn } from "@/lib/utils";

const nav = [
  { href: "/", label: "首页", icon: Home },
  { href: "/words", label: "词库", icon: BookOpen },
  { href: "/scenarios", label: "场景", icon: Layers },
  { href: "/generate", label: "生成", icon: Sparkles },
  { href: "/progress", label: "进度", icon: LineChart },
  { href: "/settings", label: "设置", icon: Settings },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-white/40 bg-white/70 shadow-sm backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-hero-gradient text-white shadow-md transition-transform group-hover:scale-105">
            <GraduationCap className="h-5 w-5" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-display text-base font-bold text-slate-900">SceneEnglish</span>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-brand-600">CET-4 / CET-6</span>
          </div>
        </Link>
        <nav className="flex items-center gap-0.5 rounded-2xl border border-white/50 bg-white/50 p-1 shadow-sm backdrop-blur-sm">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-1.5 rounded-xl px-2.5 py-2 text-sm font-medium transition-all sm:px-3",
                  active
                    ? "bg-hero-gradient text-white shadow-md"
                    : "text-slate-600 hover:bg-white hover:text-brand-700",
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden md:inline">{label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
