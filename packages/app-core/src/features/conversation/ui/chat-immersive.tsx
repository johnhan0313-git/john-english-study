"use client";

import { useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useParams } from "../../../platform/context";
import { useEffect } from "react";
import { Mic, MicOff, PhoneOff, Sparkles } from "lucide-react";
import { api } from "@sceneenglish/api-client";
import { getConversationChineseHint, conversationCopy } from "../model";
import { resolveConversationVisuals } from "../model";
import { cn } from "../../../app-chrome/utils";
import { Alert, Button, Spinner } from "../../../app-chrome/ui";
import { TalkingPortrait } from "./talking-portrait";
import { formatCallTime, useVoiceTurn } from "../hooks/use-voice-turn";

export default function ChatImmersivePage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const id = Number(sessionId);

  const { data, isLoading } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => api.getConversation(id),
  });

  const voice = useVoiceTurn({
    sessionId: id,
    enabled: data?.status === "active",
    showChineseHint: data ? getConversationChineseHint(data.scene_brief) : true,
  });

  const { playOpeningIfNeeded, started } = voice;

  useEffect(() => {
    if (!started) return;
    playOpeningIfNeeded(data?.messages, data?.status ?? "active");
  }, [data?.messages, data?.status, playOpeningIfNeeded, started]);

  if (isLoading || !data) return <Spinner label={conversationCopy.loadingImmersive} />;

  const visuals = resolveConversationVisuals(data);

  if (!voice.started) {
    return (
      <div className="relative -mx-4 -mt-2 flex min-h-[calc(100vh-var(--header-height))] items-center justify-center overflow-hidden sm:-mx-6">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={visuals.backgroundUrl}
          alt=""
          className="absolute inset-0 h-full w-full object-cover animate-scene-kenburns"
          onError={(e) => {
            e.currentTarget.src = "/scenes/default.svg";
          }}
        />
        <div className="absolute inset-0 z-[1] bg-slate-900/55" />
        <div className="relative z-20 mx-4 max-w-md space-y-5 rounded-2xl border border-white/20 bg-white/10 p-8 text-center backdrop-blur-md">
          <Sparkles className="mx-auto h-10 w-10 text-brand-200" />
          <h1 className="text-2xl font-bold text-white">沉浸式角色对话</h1>
          <p className="text-sm leading-relaxed text-white/80">
            与 <span className="font-semibold text-white">{visuals.roleLabel}</span> 在
            {visuals.ambientLabel} 场景中练习英语。角色会根据语音实时口型动画。
          </p>
          <Button
            type="button"
            size="lg"
            className="relative z-20 w-full"
            onClick={() => voice.unlockAndStart(data.messages, data.status)}
          >
            开始沉浸对话
          </Button>
          <Link href={`/chat/${id}`} className="block text-sm text-white/70 hover:text-white">
            返回文字对话
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="relative -mx-4 -mt-2 flex min-h-[calc(100vh-var(--header-height))] flex-col overflow-hidden sm:-mx-6">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={visuals.backgroundUrl}
        alt=""
        className="absolute inset-0 h-full w-full object-cover animate-scene-kenburns"
        onError={(e) => {
          e.currentTarget.src = "/scenes/default.svg";
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-900/40 via-slate-900/20 to-slate-900/75" />

      <div className="relative z-10 flex shrink-0 items-center justify-between px-4 py-3 text-white">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-200">沉浸模式</p>
          <h1 className="text-lg font-bold">{data.title}</h1>
          <p className="text-xs text-white/70">
            {visuals.ambientLabel} · {formatCallTime(voice.elapsed)}
          </p>
        </div>
        <Link href={`/chat/${id}`}>
          <button
            type="button"
            className="flex h-11 w-11 items-center justify-center rounded-full bg-red-500/90 text-white shadow-lg hover:bg-red-600"
            aria-label="挂断"
          >
            <PhoneOff className="h-5 w-5" />
          </button>
        </Link>
      </div>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-end px-4 pb-6 pt-2">
        <TalkingPortrait
          portraitUrl={visuals.portraitUrl}
          roleLabel={visuals.roleLabel}
          isSpeaking={voice.playing}
          mouthOpen={voice.mouthOpen}
          viseme={voice.viseme}
          className="mb-4"
        />

        <div className="w-full max-w-lg space-y-4">
          <div className="min-h-[5rem] rounded-2xl border border-white/20 bg-black/40 px-4 py-3 text-left reading-text text-white whitespace-pre-wrap backdrop-blur-sm">
            {voice.subtitle || conversationCopy.waitingForPartner}
          </div>

          {voice.error && <Alert variant="warning">{voice.error}</Alert>}

          {voice.processing && (
            <p className="text-center text-sm text-white/70">识别与回复中...</p>
          )}
          {voice.playing && (
            <p className="text-center text-sm text-brand-200">对方正在说话...</p>
          )}

          {data.status === "active" && (
            <div className="flex flex-col items-center gap-3">
              <button
                type="button"
                disabled={voice.playing || voice.processing}
                onMouseDown={() => void voice.startRecording()}
                onMouseUp={voice.stopRecording}
                onMouseLeave={() => voice.recording && voice.stopRecording()}
                onTouchStart={() => void voice.startRecording()}
                onTouchEnd={voice.stopRecording}
                className={cn(
                  "flex h-16 w-16 items-center justify-center rounded-full transition-all shadow-lg",
                  voice.recording ? "bg-red-500 text-white scale-110" : "bg-white/90 text-brand-700 hover:bg-white",
                  (voice.playing || voice.processing) && "opacity-50",
                )}
              >
                {voice.recording ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
              </button>
              <p className="text-xs text-white/60">按住麦克风说话，松开后发送</p>
            </div>
          )}

          <div className="flex justify-center gap-4 text-sm">
            <Link href={`/chat/${id}/call`} className="text-white/70 hover:text-white">
              普通电话模式
            </Link>
            <Link href={`/chat/${id}`} className="text-white/70 hover:text-white">
              文字对话
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
