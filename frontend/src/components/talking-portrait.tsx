"use client";

import { cn } from "@/lib/utils";
import type { MouthShape } from "@/hooks/use-lipsync-audio";
import { visemeToMouthShape } from "@/hooks/use-lipsync-audio";
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

function mouthStyles(shape: MouthShape, open: number) {
  const width = {
    closed: 22,
    slight: 24 + open * 8,
    medium: 28 + open * 14,
    wide: 34 + open * 18,
    round: 18 + open * 10,
    smile: 30 + open * 12,
  }[shape];

  const height = {
    closed: 3,
    slight: 6 + open * 10,
    medium: 10 + open * 16,
    wide: 14 + open * 22,
    round: 16 + open * 14,
    smile: 8 + open * 8,
  }[shape];

  return { width, height, borderRadius: shape === "round" ? "9999px" : shape === "smile" ? "0 0 9999px 9999px" : "9999px" };
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

  return (
    <div className={cn("relative mx-auto w-full max-w-xs", className)}>
      <div
        className={cn(
          "relative transition-transform duration-700",
          isSpeaking ? "animate-[portrait-talk_2s_ease-in-out_infinite]" : "animate-[portrait-idle_4s_ease-in-out_infinite]",
          blink && "scale-y-[0.98]",
        )}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={portraitUrl}
          alt={roleLabel}
          className="mx-auto h-auto w-full max-h-[320px] object-contain drop-shadow-2xl"
          onError={(e) => {
            e.currentTarget.src = "/avatars/default.svg";
          }}
        />

        <div
          className="absolute left-1/2 -translate-x-1/2 transition-all duration-75"
          style={{
            top: "52%",
            width: mouth.width,
            height: mouth.height,
            borderRadius: mouth.borderRadius,
            backgroundColor: isSpeaking && mouthOpen > 0.08 ? "#7c2d12" : "#92400e",
            opacity: isSpeaking ? 0.95 : 0.85,
          }}
        />
      </div>

      <p className="mt-3 text-center text-sm font-medium text-white/90 drop-shadow-md">{roleLabel}</p>
    </div>
  );
}
