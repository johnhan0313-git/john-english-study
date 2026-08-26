"use client";

import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useEffect, useRef, useState } from "react";
import { ChevronDown, LineChart, LogOut, User } from "lucide-react";

import { Button } from "../../../app-chrome/ui";
import { useAuth } from "../auth-context";
import { cn } from "../../../app-chrome/utils";
import { resolveAvatarUrl } from "@sceneenglish/api-client";

export function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  if (!user) return null;

  const avatarSrc = resolveAvatarUrl(user.avatar_url);
  const displayName = user.display_name || user.username;

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-haspopup="menu"
        className={cn(
          "flex items-center gap-2 rounded-xl border border-surface-border/80 bg-white px-2 py-1.5 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-brand-200 hover:bg-brand-50/50 hover:text-brand-700",
          open && "border-brand-200 bg-brand-50/50 text-brand-700",
        )}
      >
        <img src={avatarSrc} alt="" className="h-7 w-7 rounded-full object-cover" />
        <span className="hidden max-w-[8rem] truncate sm:inline">{displayName}</span>
        <ChevronDown className={cn("h-4 w-4 shrink-0 text-slate-400 transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div
          role="menu"
          className="absolute right-0 z-50 mt-2 min-w-[10rem] overflow-hidden rounded-xl border border-surface-border/80 bg-white py-1 shadow-lg"
        >
          <Link
            href="/profile"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-brand-50 hover:text-brand-700"
          >
            <User className="h-4 w-4" />
            个人中心
          </Link>
          <Link
            href="/progress"
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-brand-50 hover:text-brand-700"
          >
            <LineChart className="h-4 w-4" />
            学习进度
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              logout();
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-slate-700 hover:bg-red-50 hover:text-red-600"
          >
            <LogOut className="h-4 w-4" />
            退出登录
          </button>
        </div>
      )}
    </div>
  );
}

export function AuthNavActions() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return null;
  if (isAuthenticated) return <UserMenu />;

  return (
    <div className="flex items-center gap-2">
      <Link href="/login">
        <Button size="sm">登录</Button>
      </Link>
    </div>
  );
}
