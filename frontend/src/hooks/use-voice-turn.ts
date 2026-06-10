"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { ApiError, fetchAuthenticatedAudioBlobUrl } from "@/lib/api/client";
import { useLipsyncAudio } from "@/hooks/use-lipsync-audio";

interface UseVoiceTurnOptions {
  sessionId: number;
  enabled?: boolean;
  autoPlayOpening?: boolean;
  initialStarted?: boolean;
  showChineseHint?: boolean;
}

export function useVoiceTurn({
  sessionId,
  enabled = true,
  autoPlayOpening = true,
  initialStarted = false,
  showChineseHint = true,
}: UseVoiceTurnOptions) {
  const queryClient = useQueryClient();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const blobUrlRef = useRef<string | null>(null);
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

  const revokeBlobUrl = useCallback(() => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
  }, []);

  const ensureAudio = useCallback(() => {
    if (!audioRef.current) {
      const audio = new Audio();
      audio.setAttribute("playsinline", "true");
      audioRef.current = audio;
    }
    return audioRef.current;
  }, []);

  const playAudio = useCallback(
    async (url: string) => {
      const audio = ensureAudio();
      stopAnalysis();
      revokeBlobUrl();
      setPlaying(true);
      setError(null);

      try {
        const playUrl = await fetchAuthenticatedAudioBlobUrl(url);
        blobUrlRef.current = playUrl;

        audio.onended = () => {
          setPlaying(false);
          stopAnalysis();
          revokeBlobUrl();
        };
        audio.onerror = () => {
          setPlaying(false);
          stopAnalysis();
          revokeBlobUrl();
          setError("语音播放失败");
        };
        audio.onplay = () => connect(audio);
        audio.src = playUrl;
        await audio.play();
      } catch (e) {
        setPlaying(false);
        stopAnalysis();
        revokeBlobUrl();
        if (e instanceof ApiError) {
          if (e.status === 503) {
            setError("语音合成未配置或暂时不可用");
          } else {
            setError(e.message || "语音加载失败");
          }
        } else {
          setError("无法播放语音，请允许浏览器自动播放");
        }
      }
    },
    [connect, ensureAudio, revokeBlobUrl, stopAnalysis],
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
        const result = await api.sendVoiceTurn(sessionId, blob, showChineseHint);
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
  }, [enabled, playAudio, playing, processing, queryClient, sessionId, showChineseHint]);

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
      revokeBlobUrl();
    },
    [revokeBlobUrl, stopAnalysis],
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
