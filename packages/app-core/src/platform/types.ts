import type { ComponentType, ReactNode } from "react";

export type RuntimePlatform =
  | "web"
  | "ios"
  | "android"
  | "macos"
  | "windows"
  | "wechat"
  | "alipay"
  | "douyin";

export interface PlatformLinkProps {
  href: string;
  className?: string;
  children: ReactNode;
  onClick?: () => void;
  prefetch?: boolean;
  role?: string;
  onMouseEnter?: () => void;
  onFocus?: () => void;
}

export interface PlatformStorage {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
}

export interface PlatformRecorder {
  start(): Promise<void>;
  stop(): Promise<Blob>;
}

export interface PlatformAudio {
  play(url: string): Promise<void>;
  setRate(rate: number): void;
  pause(): void;
  /** Browser DOM element for lipsync/analysis; null on non-DOM runtimes. */
  getElement?(): HTMLAudioElement | null;
  setOnEnded?(cb: (() => void) | null): void;
  setOnError?(cb: (() => void) | null): void;
  setOnPlay?(cb: ((el: HTMLAudioElement) => void) | null): void;
}

export interface PlatformNavigation {
  navigate(path: string, opts?: { replace?: boolean; scroll?: boolean }): void;
  useParams<T extends Record<string, string>>(): T;
  useSearchParams(): URLSearchParams;
  usePathname(): string;
  Link: ComponentType<PlatformLinkProps>;
  prefetch?(path: string): void;
}

export interface PlatformServices {
  navigation: PlatformNavigation;
  storage: PlatformStorage;
  getDeviceId(): Promise<string>;
  getApiBase(): string;
  getRuntime(): RuntimePlatform;
  openExternal(url: string): void;
  recorder: PlatformRecorder;
  audio: PlatformAudio;
  onUnauthorized?(): void;
}
