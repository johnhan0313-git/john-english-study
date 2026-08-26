"use client";

import { Loader2, Pause, Volume2 } from "lucide-react";
import { cn } from "./utils";
import type { AudioPlayer } from "./use-audio-player";

type AudioPlayButtonProps = {
  audioKey: string;
  url: string;
  player: AudioPlayer;
  size?: "sm" | "md";
  label?: string;
  className?: string;
  onClick?: (e: React.MouseEvent) => void;
};

export function AudioPlayButton({
  audioKey,
  url,
  player,
  size = "sm",
  label,
  className,
  onClick,
}: AudioPlayButtonProps) {
  const playing = player.isPlaying(audioKey);
  const loading = player.isLoading(audioKey);

  const handleClick = (e: React.MouseEvent) => {
    onClick?.(e);
    void player.toggle(url, audioKey);
  };

  const sizes = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
  };

  const iconSizes = {
    sm: "h-4 w-4",
    md: "h-5 w-5",
  };

  return (
    <button
      type="button"
      title={label ?? (playing ? "暂停" : "播放")}
      aria-label={label ?? (playing ? "暂停" : "播放")}
      onClick={handleClick}
      disabled={loading}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full border transition-all",
        playing
          ? "border-brand-300 bg-brand-100 text-brand-700 shadow-sm"
          : "border-surface-border bg-white text-brand-600 hover:border-brand-200 hover:bg-brand-50",
        loading && "opacity-70",
        sizes[size],
        className,
      )}
    >
      {loading ? (
        <Loader2 className={cn(iconSizes[size], "animate-spin")} />
      ) : playing ? (
        <Pause className={iconSizes[size]} />
      ) : (
        <Volume2 className={iconSizes[size]} />
      )}
    </button>
  );
}
