"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@sceneenglish/api-client";
import { ApiError, parseApiError } from "@sceneenglish/api-client";

import { fetchAuthenticatedAudioBlobUrl } from "../../../app-chrome/audio";
import { usePlatform } from "../../../platform/context";
import { useLipsyncAudio } from "./use-lipsync-audio";
import { voiceCopy, type VoiceTurnPhase, voicePhaseFlags } from "../model";

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
  const { recorder, audio: platformAudio } = usePlatform();
  const blobUrlRef = useRef<string | null>(null);
  const openingPlayedRef = useRef(false);

  const [phase, setPhase] = useState<VoiceTurnPhase>({ kind: "idle" });
  const [subtitle, setSubtitle] = useState("");
  const [started, setStarted] = useState(initialStarted);
  const [elapsed, setElapsed] = useState(0);

  const flags = voicePhaseFlags(phase);
  const { recording, processing, playing, error } = flags;

  const { connect, stopAnalysis, mouthOpen, viseme } = useLipsyncAudio();

  const revokeBlobUrl = useCallback(() => {
    if (blobUrlRef.current) {
      URL.revokeObjectURL(blobUrlRef.current);
      blobUrlRef.current = null;
    }
  }, []);

  const playAudio = useCallback(
    async (url: string) => {
      stopAnalysis();
      revokeBlobUrl();
      setPhase({ kind: "playing" });

      try {
        const playUrl = await fetchAuthenticatedAudioBlobUrl(url);
        blobUrlRef.current = playUrl;

        platformAudio.setOnEnded?.(() => {
          setPhase({ kind: "idle" });
          stopAnalysis();
          revokeBlobUrl();
        });
        platformAudio.setOnError?.(() => {
          setPhase({ kind: "error", message: voiceCopy.playFailed });
          stopAnalysis();
          revokeBlobUrl();
        });
        platformAudio.setOnPlay?.((el) => connect(el));

        await platformAudio.play(playUrl);
      } catch (e) {
        stopAnalysis();
        revokeBlobUrl();
        if (e instanceof ApiError) {
          if (e.status === 503) {
            setPhase({ kind: "error", message: voiceCopy.ttsUnavailable });
          } else {
            setPhase({ kind: "error", message: e.message || "语音加载失败" });
          }
        } else {
          setPhase({ kind: "error", message: "无法播放语音，请允许浏览器自动播放" });
        }
      }
    },
    [connect, platformAudio, revokeBlobUrl, stopAnalysis],
  );

  const playOpening = useCallback(
    (
      messages: { id: number; role: string; content: string }[],
      status: string,
    ) => {
      if (!autoPlayOpening || !messages.length || openingPlayedRef.current) return;
      const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
      if (!lastAssistant) {
        setPhase({ kind: "error", message: "未找到 AI 开场消息" });
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
      setPhase({ kind: "idle" });
      if (!messages?.length) {
        setPhase({ kind: "error", message: "暂无对话消息，请返回重新开始" });
        return;
      }
      playOpening(messages, status ?? "active");
    },
    [playOpening],
  );

  const startRecording = useCallback(async () => {
    if (!enabled || playing || processing) return;
    try {
      await recorder.start();
      setPhase({ kind: "recording" });
    } catch {
      setPhase({ kind: "error", message: "无法开始录音，请允许麦克风权限" });
    }
  }, [enabled, playing, processing, recorder]);

  const stopRecording = useCallback(async () => {
    if (!recording) return;
    setPhase({ kind: "processing" });
    try {
      const blob = await recorder.stop();
      const result = await api.sendVoiceTurn(sessionId, blob, showChineseHint);
      setSubtitle(`${result.transcript}\n\n— ${result.content}`);
      await queryClient.invalidateQueries({ queryKey: ["conversation", sessionId] });
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      playAudio(result.audio_url);
    } catch (e) {
      setPhase({ kind: "error", message: parseApiError(e, "语音发送失败") });
    }
  }, [playAudio, queryClient, recorder, recording, sessionId, showChineseHint]);

  useEffect(() => {
    if (!started) return;
    const timer = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => window.clearInterval(timer);
  }, [started]);

  useEffect(
    () => () => {
      stopAnalysis();
      platformAudio.pause();
      revokeBlobUrl();
    },
    [platformAudio, revokeBlobUrl, stopAnalysis],
  );

  return {
    audioRef: { current: platformAudio.getElement?.() ?? null },
    phase,
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
