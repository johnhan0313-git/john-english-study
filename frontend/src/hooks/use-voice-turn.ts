"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useLipsyncAudio } from "@/hooks/use-lipsync-audio";

interface UseVoiceTurnOptions {
  sessionId: number;
  enabled?: boolean;
  autoPlayOpening?: boolean;
  initialStarted?: boolean;
}

export function useVoiceTurn({
  sessionId,
  enabled = true,
  autoPlayOpening = true,
  initialStarted = false,
}: UseVoiceTurnOptions) {
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const openingPlayedRef = useRef(false);

  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [subtitle, setSubtitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [started, setStarted] = useState(initialStarted);
  const [elapsed, setElapsed] = useState(0);

  const { connect, stopAnalysis, mouthOpen, viseme } = useLipsyncAudio();

  const ensureAudio = useCallback(() => {
    if (!audioRef.current) {
      const audio = new Audio();
      audio.setAttribute("playsinline", "true");
      audioRef.current = audio;
    }
    return audioRef.current;
  }, []);

  const playAudio = useCallback(
    (url: string) => {
      const audio = ensureAudio();
      stopAnalysis();
      setPlaying(true);
      setError(null);
      audio.onended = () => {
        setPlaying(false);
        stopAnalysis();
      };
      audio.onerror = () => {
        setPlaying(false);
        stopAnalysis();
        setError("语音加载失败，请检查后端是否已启动");
      };
      audio.onplay = () => connect(audio);
      audio.src = url;
      void audio.play().catch(() => {
        setPlaying(false);
        stopAnalysis();
        setError("无法播放语音，请允许浏览器自动播放");
      });
    },
    [connect, ensureAudio, stopAnalysis],
  );

  const playOpening = useCallback(
    (
      messages: { id: number; role: string; content: string }[],
      status: string,
    ) => {
      if (!autoPlayOpening || !messages.length || openingPlayedRef.current) return;
      const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
      if (!lastAssistant) {
        setError("未找到 AI 开场消息");
        return;
      }
      openingPlayedRef.current = true;
      setSubtitle(lastAssistant.content);
      if (status === "active") {
        playAudio(api.getConversationMessageAudioUrl(sessionId, lastAssistant.id));
      }
    },
    [autoPlayOpening, playAudio, sessionId],
  );

  const playOpeningIfNeeded = useCallback(
    (
      messages: { id: number; role: string; content: string }[] | undefined,
      status: string,
    ) => {
      if (!messages?.length || !started) return;
      playOpening(messages, status);
    },
    [playOpening, started],
  );

  const unlockAndStart = useCallback(
    (messages?: { id: number; role: string; content: string }[], status?: string) => {
      setStarted(true);
      setError(null);
      if (!messages?.length) {
        setError("暂无对话消息，请返回重新开始");
        return;
      }
      playOpening(messages, status ?? "active");
    },
    [playOpening],
  );

  const startRecording = useCallback(async () => {
    if (!enabled || playing || processing) return;
    setError(null);
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      setProcessing(true);
      try {
        const result = await api.sendVoiceTurn(sessionId, blob);
        setSubtitle(`${result.transcript}\n\n— ${result.content}`);
        await queryClient.invalidateQueries({ queryKey: ["conversation", sessionId] });
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
        playAudio(result.audio_url);
      } catch (e) {
        setError(e instanceof Error ? e.message : "语音发送失败");
      } finally {
        setProcessing(false);
      }
    };
    recorder.start();
    mediaRecorderRef.current = recorder;
    setRecording(true);
  }, [enabled, playAudio, playing, processing, queryClient, sessionId]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  }, []);

  useEffect(() => {
    if (!started) return;
    const timer = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => window.clearInterval(timer);
  }, [started]);

  useEffect(
    () => () => {
      stopAnalysis();
      audioRef.current?.pause();
    },
    [stopAnalysis],
  );

  return {
    audioRef,
    recording,
    processing,
    playing,
    subtitle,
    setSubtitle,
    error,
    started,
    elapsed,
    mouthOpen,
    viseme,
    unlockAndStart,
    playOpeningIfNeeded,
    playAudio,
    startRecording,
    stopRecording,
    openingPlayedRef,
  };
}

export function formatCallTime(sec: number): string {
  const m = Math.floor(sec / 60).toString().padStart(2, "0");
  const s = (sec % 60).toString().padStart(2, "0");
  return `${m}:${s}`;
}
