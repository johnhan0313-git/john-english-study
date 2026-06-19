"use client";

import { useQueryClient } from "@tanstack/react-query";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { authApi } from "@sceneenglish/api-client";
import type { AuthUser } from "@sceneenglish/api-client";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
  useNavigate,
  usePlatform,
} from "@sceneenglish/app-core/platform/context";

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  loginWithEmail: (
    email: string,
    code: string,
    captcha: { captcha_id: string; captcha_x: number },
  ) => Promise<void>;
  finishOAuthLogin: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const platform = usePlatform();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const mergeLegacyDevice = useCallback(async () => {
    const deviceId = await platform.getDeviceId();
    try {
      await authApi.mergeDevice(deviceId);
    } catch {
      // merge is best-effort
    }
  }, [platform]);

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
      await clearAccessToken(platform);
      setUser(null);
    }
  }, [platform]);

  const finishAuth = useCallback(
    async (token: string) => {
      await setAccessToken(platform, token);
      await mergeLegacyDevice();
      await refreshUser();
      queryClient.invalidateQueries();
    },
    [platform, mergeLegacyDevice, refreshUser, queryClient],
  );

  const loginWithEmail = useCallback(
    async (email: string, code: string, captcha: { captcha_id: string; captcha_x: number }) => {
      const res = await authApi.emailLogin({ email, code, ...captcha });
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
    void clearAccessToken(platform);
    setUser(null);
    queryClient.clear();
    navigate("/");
  }, [platform, queryClient, navigate]);

  useEffect(() => {
    refreshUser().finally(() => setIsLoading(false));
  }, [refreshUser]);

  useEffect(() => {
    const onUnauthorized = () => {
      void clearAccessToken(platform);
      setUser(null);
      const next = encodeURIComponent(window.location.pathname);
      navigate(`/login?next=${next}`);
    };
    window.addEventListener("auth:unauthorized", onUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", onUnauthorized);
  }, [platform, navigate]);

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
