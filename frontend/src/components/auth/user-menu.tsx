"use client";

import Link from "next/link";
import { LogOut, Settings, User } from "lucide-react";

import { Button } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";

export function UserMenu() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="hidden items-center gap-1.5 text-sm font-medium text-slate-700 sm:inline-flex">
        <User className="h-4 w-4 text-brand-600" />
        {user.display_name || user.username}
      </span>
      <Link href="/settings">
        <Button variant="ghost" size="sm" className="px-2">
          <Settings className="h-4 w-4" />
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
        <Button variant="ghost" size="sm">
          登录
        </Button>
      </Link>
      <Link href="/register">
        <Button size="sm">注册</Button>
      </Link>
    </div>
  );
}
