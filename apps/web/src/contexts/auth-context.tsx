"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { authApi } from "@/lib/auth/api";
import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/auth/token";
import type { AuthUser } from "@/lib/auth/types";
import { getDeviceId } from "@/lib/utils";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  loginWithEmail: (email: string, code: string) => Promise<void>;
  finishOAuthLogin: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function mergeLegacyDevice() {
  const deviceId = getDeviceId();
  if (!deviceId) return;
  try {
    await authApi.mergeDevice(deviceId);
  } catch {
    // merge is best-effort
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      return;
    }
    try {
      const me = await authApi.me();
      setUser(me);
    } catch {
      clearAccessToken();
      setUser(null);
    }
  }, []);

  const finishAuth = useCallback(
    async (token: string) => {
      setAccessToken(token);
      await mergeLegacyDevice();
      await refreshUser();
      queryClient.invalidateQueries();
    },
    [queryClient, refreshUser],
  );

  const loginWithEmail = useCallback(
    async (email: string, code: string) => {
      const res = await authApi.emailLogin({ email, code });
      await finishAuth(res.access_token);
    },
    [finishAuth],
  );

  const finishOAuthLogin = useCallback(
    async (token: string) => {
      await finishAuth(token);
    },
    [finishAuth],
  );

  const logout = useCallback(() => {
    clearAccessToken();
    setUser(null);
    queryClient.clear();
    router.push("/");
  }, [queryClient, router]);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  useEffect(() => {
    const onUnauthorized = () => {
      clearAccessToken();
      setUser(null);
      const next = encodeURIComponent(window.location.pathname);
      router.push(`/login?next=${next}`);
    };
    window.addEventListener("auth:unauthorized", onUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", onUnauthorized);
  }, [router]);

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      loginWithEmail,
      finishOAuthLogin,
      logout,
      refreshUser,
    }),
    [user, isLoading, loginWithEmail, finishOAuthLogin, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
