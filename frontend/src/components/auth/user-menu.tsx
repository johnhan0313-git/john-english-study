"use client";

import Link from "next/link";
import { LogOut, User } from "lucide-react";

import { Button } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";
import { resolveAvatarUrl } from "@/lib/profile/api";

export function UserMenu() {
  const { user, logout } = useAuth();
  if (!user) return null;

  const avatarSrc = resolveAvatarUrl(user.avatar_url);

  return (
    <div className="flex items-center gap-2">
      <Link
        href="/profile"
        className="hidden items-center gap-1.5 text-sm font-medium text-slate-700 hover:text-brand-700 sm:inline-flex"
      >
        <img src={avatarSrc} alt="" className="h-6 w-6 rounded-full object-cover" />
        {user.display_name || user.username}
      </Link>
      <Link href="/profile" className="sm:hidden">
        <Button variant="ghost" size="sm" className="px-2" aria-label="个人中心">
          <User className="h-4 w-4 text-brand-600" />
        </Button>
      </Link>
      <Button variant="outline" size="sm" onClick={logout}>
        <LogOut className="mr-1 h-3.5 w-3.5" />
        退出
      </Button>
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
