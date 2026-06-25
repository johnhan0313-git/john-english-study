"use client";

import { cn } from "@sceneenglish/app-core/lib/utils";
import type { MouthShape } from "@sceneenglish/app-core/hooks/use-lipsync-audio";
import { visemeToMouthShape } from "@sceneenglish/app-core/hooks/use-lipsync-audio";
import { VISEMES } from "wawa-lipsync";
import { useEffect, useState } from "react";

interface TalkingPortraitProps {
  portraitUrl: string;
  roleLabel: string;
  isSpeaking: boolean;
  mouthOpen: number;
  viseme?: VISEMES;
  className?: string;
}

const PORTRAIT_MOUTH_TOP_PERCENT = (112 / 260) * 100;

function mouthStyles(shape: MouthShape, open: number) {
  const width = {
    closed: 20,
    slight: 22 + open * 10,
    medium: 26 + open * 16,
    wide: 32 + open * 20,
    round: 16 + open * 12,
    smile: 28 + open * 14,
  }[shape];

  const height = {
    closed: 2,
    slight: 5 + open * 12,
    medium: 9 + open * 18,
    wide: 12 + open * 24,
    round: 14 + open * 16,
    smile: 7 + open * 10,
  }[shape];

  return {
    width,
    height,
    borderRadius: shape === "round" ? "9999px" : shape === "smile" ? "0 0 9999px 9999px" : "9999px",
  };
}

export function TalkingPortrait({
  portraitUrl,
  roleLabel,
  isSpeaking,
  mouthOpen,
  viseme = VISEMES.sil,
  className,
}: TalkingPortraitProps) {
  const [blink, setBlink] = useState(false);

  useEffect(() => {
    if (isSpeaking) return;
    const scheduleBlink = () => {
      const delay = 2500 + Math.random() * 3500;
      return window.setTimeout(() => {
        setBlink(true);
        window.setTimeout(() => setBlink(false), 140);
        timer = scheduleBlink();
      }, delay);
    };
    let timer = scheduleBlink();
    return () => window.clearTimeout(timer);
  }, [isSpeaking]);

  const shape = visemeToMouthShape(viseme);
  const mouth = mouthStyles(shape, isSpeaking ? mouthOpen : 0);
  const showMouth = isSpeaking && mouthOpen > 0.06;

  return (
    <div className={cn("relative mx-auto w-full max-w-[280px]", className)} style={{ perspective: "900px" }}>
      <div
        className={cn(
          "pointer-events-none absolute left-1/2 top-[42%] h-40 w-40 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-300/25 blur-3xl",
          isSpeaking && "animate-pulse bg-brand-200/40",
        )}
        aria-hidden
      />

      <div
        className={cn(
          "relative transition-transform duration-500 [transform-style:preserve-3d]",
          isSpeaking
            ? "animate-[portrait-talk_2s_ease-in-out_infinite] scale-[1.02]"
            : "animate-[portrait-idle_4s_ease-in-out_infinite]",
          blink && "scale-y-[0.98]",
        )}
      >
        <div
          className={cn(
            "overflow-hidden rounded-[2rem] border bg-gradient-to-b from-white/15 to-white/5 p-2 shadow-[0_20px_50px_rgba(0,0,0,0.35)] ring-1 backdrop-blur-sm transition-all duration-300",
            isSpeaking
              ? "border-brand-200/40 ring-brand-200/30 shadow-[0_24px_60px_rgba(255,173,138,0.2)]"
              : "border-white/20 ring-white/15",
          )}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={portraitUrl}
            alt={roleLabel}
            className="mx-auto h-auto w-full max-h-[300px] object-contain"
            onError={(e) => {
              e.currentTarget.src = "/avatars/default.svg";
            }}
          />
        </div>

        {showMouth && (
          <div
            className="absolute left-1/2 -translate-x-1/2 transition-all duration-75"
            style={{
              top: `${PORTRAIT_MOUTH_TOP_PERCENT}%`,
              width: mouth.width,
              height: mouth.height,
              borderRadius: mouth.borderRadius,
              backgroundColor: "#991b1b",
              boxShadow: "0 0 0 2px rgba(253, 164, 175, 0.85), inset 0 1px 2px rgba(0,0,0,0.2)",
            }}
          />
        )}
      </div>

      <p className="mt-4 text-center text-sm font-semibold tracking-wide text-white drop-shadow-md">
        {roleLabel}
      </p>
    </div>
  );
}
