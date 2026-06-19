import { useCallback, useEffect, useRef, useState } from "react";

export function useAudioPlayer() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const audio = new Audio();
    audio.onended = () => setActiveKey(null);
    audioRef.current = audio;
    return () => {
      audio.pause();
      audioRef.current = null;
    };
  }, []);

  const toggle = useCallback(
    async (url: string, key: string) => {
      const audio = audioRef.current;
      if (!audio) return;

      if (activeKey === key && !audio.paused) {
        audio.pause();
        audio.currentTime = 0;
        setActiveKey(null);
        return;
      }

      setError(null);
      setLoadingKey(key);
      audio.pause();
      audio.src = url;

      try {
        await audio.play();
        setActiveKey(key);
      } catch {
        setError("播放失败，请检查网络或稍后重试");
        setActiveKey(null);
      } finally {
        setLoadingKey(null);
      }
    },
    [activeKey],
  );

  const isPlaying = useCallback(
    (key: string) => activeKey === key && loadingKey !== key,
    [activeKey, loadingKey],
  );

  const isLoading = useCallback((key: string) => loadingKey === key, [loadingKey]);

  return { toggle, isPlaying, isLoading, error, activeKey };
}

export type AudioPlayer = ReturnType<typeof useAudioPlayer>;
