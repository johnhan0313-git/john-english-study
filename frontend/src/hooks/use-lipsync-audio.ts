"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Lipsync, VISEMES } from "wawa-lipsync";

export type MouthShape = "closed" | "slight" | "medium" | "wide" | "round" | "smile";

export function visemeToMouthShape(viseme: VISEMES): MouthShape {
  switch (viseme) {
    case VISEMES.sil:
    case VISEMES.PP:
    case VISEMES.FF:
      return "closed";
    case VISEMES.U:
    case VISEMES.CH:
      return "round";
    case VISEMES.aa:
    case VISEMES.O:
      return "wide";
    case VISEMES.E:
    case VISEMES.I:
      return "smile";
    case VISEMES.TH:
    case VISEMES.DD:
    case VISEMES.kk:
    case VISEMES.SS:
    case VISEMES.nn:
    case VISEMES.RR:
      return "medium";
    default:
      return "slight";
  }
}

export function mouthShapeToOpenAmount(shape: MouthShape, volume: number): number {
  const base = {
    closed: 0.05,
    slight: 0.25,
    medium: 0.45,
    wide: 0.75,
    round: 0.55,
    smile: 0.35,
  }[shape];
  return Math.min(1, base + volume * 0.4);
}

export function useLipsyncAudio() {
  const lipsyncRef = useRef<Lipsync | null>(null);
  const rafRef = useRef<number>(0);
  const [viseme, setViseme] = useState<VISEMES>(VISEMES.sil);
  const [mouthOpen, setMouthOpen] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const stopAnalysis = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = 0;
    setIsAnalyzing(false);
    setViseme(VISEMES.sil);
    setMouthOpen(0);
  }, []);

  const connect = useCallback(
    (audio: HTMLAudioElement) => {
      if (!lipsyncRef.current) lipsyncRef.current = new Lipsync();
      lipsyncRef.current.connectAudio(audio);
      stopAnalysis();
      setIsAnalyzing(true);

      const loop = () => {
        const manager = lipsyncRef.current;
        if (!manager) return;
        manager.processAudio();
        const currentViseme = manager.viseme;
        const volume = manager.features?.volume ?? 0;
        const shape = visemeToMouthShape(currentViseme);
        setViseme(currentViseme);
        setMouthOpen(mouthShapeToOpenAmount(shape, volume));
        rafRef.current = requestAnimationFrame(loop);
      };
      rafRef.current = requestAnimationFrame(loop);
    },
    [stopAnalysis],
  );

  useEffect(() => () => stopAnalysis(), [stopAnalysis]);

  return { connect, stopAnalysis, viseme, mouthOpen, isAnalyzing };
}
