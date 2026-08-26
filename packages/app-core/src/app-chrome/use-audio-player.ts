"use client";

import { useCallback, useEffect, useState } from "react";
import { usePlatform } from "../platform/context";

/** Shared keyed audio player backed by PlatformServices.audio (no raw Audio in chrome). */
export function useAudioPlayer() {
  const { audio } = usePlatform();
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    audio.setOnEnded?.(() => setActiveKey(null));
    audio.setOnError?.(() => {
      setActiveKey(null);
      setError("播放失败，请检查网络或稍后重试");
    });
    return () => {
      audio.pause();
      audio.setOnEnded?.(null);
      audio.setOnError?.(null);
    };
  }, [audio]);

  const toggle = useCallback(
    async (url: string, key: string) => {
      if (activeKey === key) {
        audio.pause();
        setActiveKey(null);
        return;
      }

      setError(null);
      setLoadingKey(key);
      try {
        await audio.play(url);
        setActiveKey(key);
      } catch {
        setError("播放失败，请检查网络或稍后重试");
        setActiveKey(null);
      } finally {
        setLoadingKey(null);
      }
    },
    [activeKey, audio],
  );

  const isPlaying = useCallback(
    (key: string) => activeKey === key && loadingKey !== key,
    [activeKey, loadingKey],
  );

  const isLoading = useCallback((key: string) => loadingKey === key, [loadingKey]);

  return { toggle, isPlaying, isLoading, error, activeKey };
}

export type AudioPlayer = ReturnType<typeof useAudioPlayer>;
