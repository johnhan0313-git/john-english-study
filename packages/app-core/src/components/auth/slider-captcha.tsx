"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import type { CaptchaData } from "@sceneenglish/api-client";

interface SliderCaptchaProps {
  data: CaptchaData;
  onComplete: (x: number) => void;
  onRefresh: () => void;
  disabled?: boolean;
  error?: string;
}

const HANDLE_SIZE = 32;
const MOVE_THRESHOLD = 4;

export function SliderCaptcha({ data, onComplete, onRefresh, disabled, error }: SliderCaptchaProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const hasMoved = useRef(false);
  const rafId = useRef<number | null>(null);
  const pendingX = useRef(0);
  const startPosition = useRef(0);

  const maxX = data.width - data.piece_width;
  const maxHandleX = data.width - HANDLE_SIZE;

  const [position, setPosition] = useState(0);
  const [draggingVisual, setDraggingVisual] = useState(false);
  const [shaking, setShaking] = useState(false);

  const clamp = useCallback((x: number) => Math.max(0, Math.min(maxX, x)), [maxX]);

  useEffect(() => {
    setPosition(0);
    hasMoved.current = false;
  }, [data.captcha_id]);

  useEffect(() => {
    if (!error) return;
    setPosition(0);
    setShaking(true);
    const timer = window.setTimeout(() => setShaking(false), 450);
    return () => window.clearTimeout(timer);
  }, [error]);

  const positionToHandleX = useCallback(
    (x: number) => (maxX > 0 ? (x / maxX) * maxHandleX : 0),
    [maxX, maxHandleX],
  );

  const clientXToPosition = useCallback(
    (clientX: number) => {
      const track = trackRef.current;
      if (!track) return 0;
      const rect = track.getBoundingClientRect();
      const handleX = Math.max(0, Math.min(maxHandleX, clientX - rect.left - HANDLE_SIZE / 2));
      return maxHandleX > 0 ? (handleX / maxHandleX) * maxX : 0;
    },
    [maxHandleX, maxX],
  );

  const schedulePosition = useCallback(
    (x: number) => {
      pendingX.current = clamp(x);
      if (rafId.current !== null) return;
      rafId.current = requestAnimationFrame(() => {
        rafId.current = null;
        setPosition(pendingX.current);
      });
    },
    [clamp],
  );

  const endDrag = useCallback(() => {
    if (!dragging.current) return;
    dragging.current = false;
    setDraggingVisual(false);

    const rounded = Math.round(clamp(pendingX.current));
    setPosition(rounded);

    if (hasMoved.current && !disabled) {
      onComplete(rounded);
    }
  }, [clamp, disabled, onComplete]);

  useEffect(() => {
    const onMove = (event: PointerEvent) => {
      if (!dragging.current || disabled) return;
      event.preventDefault();
      const next = clientXToPosition(event.clientX);
      if (Math.abs(next - startPosition.current) >= MOVE_THRESHOLD) {
        hasMoved.current = true;
      }
      schedulePosition(next);
    };
    const onUp = () => endDrag();

    window.addEventListener("pointermove", onMove, { passive: false });
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
      if (rafId.current !== null) {
        cancelAnimationFrame(rafId.current);
        rafId.current = null;
      }
    };
  }, [clientXToPosition, disabled, endDrag, schedulePosition]);

  const startDrag = (event: React.PointerEvent) => {
    if (disabled) return;
    dragging.current = true;
    hasMoved.current = false;
    setDraggingVisual(true);
    event.currentTarget.setPointerCapture(event.pointerId);
    const next = clientXToPosition(event.clientX);
    startPosition.current = next;
    schedulePosition(next);
  };

  const handleX = positionToHandleX(position);
  const fillWidth = handleX + HANDLE_SIZE / 2;

  return (
    <div className={`space-y-3 select-none ${shaking ? "animate-captcha-shake" : ""}`}>

      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-700">
          {disabled ? "验证中..." : "拖动滑块对齐拼图，松手自动验证"}
        </span>
        <button
          type="button"
          onClick={onRefresh}
          disabled={disabled}
          className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-brand-600 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${disabled ? "animate-spin" : ""}`} />
          刷新
        </button>
      </div>

      <div
        className={`relative touch-none overflow-hidden rounded-lg border border-slate-200 bg-slate-50 ${disabled ? "pointer-events-none opacity-70" : ""}`}
        style={{ width: data.width, height: data.height }}
        onPointerDown={startDrag}
      >
        <div className="pointer-events-none absolute inset-0" dangerouslySetInnerHTML={{ __html: data.background_svg }} />
        <div
          className={`pointer-events-none absolute top-0 will-change-transform ${draggingVisual ? "drop-shadow-lg" : "drop-shadow-md"}`}
          style={{
            width: data.piece_width,
            height: data.piece_width,
            top: data.puzzle_y,
            transform: `translate3d(${position}px, 0, 0)`,
            transition: draggingVisual ? "none" : "transform 200ms ease-out",
          }}
          dangerouslySetInnerHTML={{ __html: data.piece_svg }}
        />
      </div>

      <div
        ref={trackRef}
        className={`relative h-10 touch-none rounded-full border border-slate-200 bg-slate-100 ${disabled ? "pointer-events-none opacity-70" : ""}`}
        style={{ width: data.width }}
        onPointerDown={startDrag}
      >
        <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-xs text-slate-400">
          {disabled ? "请稍候" : "向右拖动 ››"}
        </div>
        <div
          className="pointer-events-none absolute inset-y-0 left-0 rounded-full bg-brand-100/80"
          style={{
            width: fillWidth,
            transition: draggingVisual ? "none" : "width 200ms ease-out",
          }}
        />
        <div
          role="slider"
          aria-valuemin={0}
          aria-valuemax={maxX}
          aria-valuenow={Math.round(position)}
          tabIndex={disabled ? -1 : 0}
          onPointerDown={startDrag}
          className={`absolute top-1/2 z-10 flex h-8 w-8 items-center justify-center rounded-full border border-brand-300 bg-white shadow-sm will-change-transform ${
            draggingVisual ? "cursor-grabbing scale-105 shadow-md ring-2 ring-brand-200" : disabled ? "cursor-wait" : "cursor-grab"
          }`}
          style={{
            transform: `translate3d(${handleX}px, -50%, 0)`,
            transition: draggingVisual ? "none" : "transform 200ms ease-out",
          }}
        >
          <span className="pointer-events-none text-brand-600">››</span>
        </div>
      </div>
    </div>
  );
}
