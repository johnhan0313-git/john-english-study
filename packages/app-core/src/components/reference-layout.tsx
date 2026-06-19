"use client";

import { PlatformLink as Link } from "./platform-link";
import { usePathname } from "../platform/navigation-hooks";
import { AudioLines, BookText } from "lucide-react";

import { PageHeader } from "./ui";
import { cn } from "../lib/utils";

const tabs = [
  { href: "/reference/phonetics", label: "音标", icon: AudioLines },
  { href: "/reference/grammar", label: "语法", icon: BookText },
];

export function ReferenceLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      <PageHeader
        badge="学习参考"
        title="音标与语法"
        description="系统梳理国际音标与 CET-4/6 核心语法，随时查阅对照"
      />

      <nav className="flex gap-1 rounded-2xl border border-surface-border/80 bg-white p-1.5 shadow-sm">
        {tabs.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition-all",
                active
                  ? "bg-hero-gradient text-white shadow-md"
                  : "text-slate-600 hover:bg-white hover:text-brand-700",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      {children}
    </div>
  );
}
