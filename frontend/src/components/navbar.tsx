"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Home, Layers, LineChart, Settings, Sparkles } from "lucide-react";
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
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-semibold text-primary-700">
          <BookOpen className="h-6 w-6" />
          <span>SceneEnglish</span>
          <span className="rounded bg-primary-100 px-2 py-0.5 text-xs text-primary-700">CET-4/6</span>
        </Link>
        <nav className="flex gap-1">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition-colors",
                pathname === href
                  ? "bg-primary-50 text-primary-700 font-medium"
                  : "text-slate-600 hover:bg-slate-50",
              )}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{label}</span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
