"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import type { CaptchaData } from "@/lib/auth/api";

interface SliderCaptchaProps {
  data: CaptchaData;
  value: number;
  onChange: (x: number) => void;
  onRefresh: () => void;
}

export function SliderCaptcha({ data, value, onChange, onRefresh }: SliderCaptchaProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const [draggingVisual, setDraggingVisual] = useState(false);

  const maxX = data.width - data.piece_width;

  const clamp = useCallback((x: number) => Math.max(0, Math.min(maxX, x)), [maxX]);

  const updateFromClientX = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track) return;
      const rect = track.getBoundingClientRect();
      const ratio = (clientX - rect.left) / rect.width;
      onChange(clamp(Math.round(ratio * maxX)));
    },
    [clamp, maxX, onChange],
  );

  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      if (!dragging.current) return;
      updateFromClientX(event.clientX);
    };
    const onUp = () => {
      dragging.current = false;
      setDraggingVisual(false);
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, [updateFromClientX]);

  const handlePointerDown = (event: React.PointerEvent) => {
    dragging.current = true;
    setDraggingVisual(true);
    event.currentTarget.setPointerCapture(event.pointerId);
    updateFromClientX(event.clientX);
  };

  const handleRatio = maxX > 0 ? value / maxX : 0;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">拖动滑块完成拼图</span>
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          刷新
        </button>
      </div>

      <div
        className="relative overflow-hidden rounded-lg border border-slate-200 bg-slate-50"
        style={{ width: data.width, height: data.height }}
      >
        <div className="absolute inset-0" dangerouslySetInnerHTML={{ __html: data.background_svg }} />
        <div
          className="pointer-events-none absolute drop-shadow-md"
          style={{ left: value, top: data.puzzle_y, width: data.piece_width, height: data.piece_width }}
          dangerouslySetInnerHTML={{ __html: data.piece_svg }}
        />
      </div>

      <div
        ref={trackRef}
        className="relative h-10 rounded-full border border-slate-200 bg-slate-100"
        style={{ width: data.width }}
      >
        <div className="absolute inset-y-0 left-3 flex items-center text-xs text-slate-400">
          按住滑块拖动
        </div>
        <div
          className="absolute inset-y-0 rounded-full bg-brand-100/80 transition-[width]"
          style={{ width: `${Math.max(12, handleRatio * 100)}%` }}
        />
        <button
          type="button"
          onPointerDown={handlePointerDown}
          className={`absolute top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-full border border-brand-300 bg-white shadow-sm transition-shadow ${
            draggingVisual ? "cursor-grabbing shadow-md ring-2 ring-brand-200" : "cursor-grab"
          }`}
          style={{ left: `calc(${handleRatio * 100}% - 16px)` }}
          aria-label="拖动滑块"
        >
          <span className="text-brand-600">››</span>
        </button>
      </div>
    </div>
  );
}
