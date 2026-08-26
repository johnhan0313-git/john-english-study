"use client";

import { useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useParams } from "../../../platform/context";
import { useEffect } from "react";
import { MessageSquare, Mic, MicOff, PhoneOff, Sparkles } from "lucide-react";
import { cn } from "../../../app-chrome/utils";
import { Alert, Card, Spinner } from "../../../app-chrome/ui";
import { formatCallTime, useVoiceTurn } from "../hooks/use-voice-turn";
import { api } from "@sceneenglish/api-client";
import { getConversationChineseHint } from "../model";

export default function ChatCallPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const id = Number(sessionId);

  const { data, isLoading } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => api.getConversation(id),
  });

  const voice = useVoiceTurn({
    sessionId: id,
    enabled: data?.status === "active",
    initialStarted: true,
    showChineseHint: data ? getConversationChineseHint(data.scene_brief) : true,
  });

  const { playOpeningIfNeeded, started } = voice;

  useEffect(() => {
    playOpeningIfNeeded(data?.messages, data?.status ?? "active");
  }, [data?.messages, data?.status, playOpeningIfNeeded, started]);

  if (isLoading || !data) return <Spinner label="连接通话..." />;

  const statusHint = voice.processing
    ? "识别与回复中..."
    : voice.playing
      ? "对方正在说话..."
      : null;

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center">
      <Card className="w-full overflow-hidden p-0 text-center">
        <div className="space-y-5 px-6 pb-5 pt-7">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">通话中</p>
            <h1 className="mt-1.5 text-xl font-bold text-slate-900">{data.title}</h1>
            <p className="mt-1 text-sm text-slate-500">
              {data.role_ai} · {formatCallTime(voice.elapsed)}
            </p>
          </div>

          <div className="mx-auto flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-accent-500 text-3xl font-semibold text-white shadow-lg">
            {data.role_ai.charAt(0)}
          </div>

          <div className="min-h-[4.5rem] rounded-xl bg-slate-50 px-4 py-3 text-left reading-text text-slate-700 whitespace-pre-wrap">
            {voice.subtitle || "等待对方发言..."}
          </div>

          {voice.error && <Alert variant="warning">{voice.error}</Alert>}
          {statusHint && <p className="text-sm text-slate-500">{statusHint}</p>}

          <div className="flex items-center justify-center gap-8 pt-1">
            <div className="flex flex-col items-center gap-2">
              <button
                type="button"
                disabled={voice.playing || voice.processing || data.status !== "active"}
                onMouseDown={() => void voice.startRecording()}
                onMouseUp={voice.stopRecording}
                onMouseLeave={() => voice.recording && voice.stopRecording()}
                onTouchStart={() => void voice.startRecording()}
                onTouchEnd={voice.stopRecording}
                className={cn(
                  "flex h-16 w-16 items-center justify-center rounded-full transition-all",
                  voice.recording
                    ? "scale-110 bg-red-500 text-white shadow-md"
                    : "bg-brand-100 text-brand-700 hover:bg-brand-200",
                  (voice.playing || voice.processing) && "opacity-50",
                )}
              >
                {voice.recording ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
              </button>
              <span className="text-xs text-slate-400">按住说话</span>
            </div>

            <div className="flex flex-col items-center gap-2">
              <Link href={`/chat/${id}`}>
                <button
                  type="button"
                  className="flex h-14 w-14 items-center justify-center rounded-full bg-red-50 text-red-600 ring-1 ring-red-100 transition hover:bg-red-100"
                  aria-label="挂断"
                >
                  <PhoneOff className="h-6 w-6" />
                </button>
              </Link>
              <span className="text-xs text-slate-400">挂断</span>
            </div>
          </div>
        </div>

        <div className="flex items-stretch border-t border-surface-border/60 bg-slate-50/50">
          <Link
            href={`/chat/${id}/immersive`}
            className="flex flex-1 items-center justify-center gap-1.5 py-3.5 text-sm text-slate-600 transition hover:bg-white hover:text-brand-700"
          >
            <Sparkles className="h-4 w-4 shrink-0" />
            沉浸模式
          </Link>
          <div className="w-px bg-surface-border/60" />
          <Link
            href={`/chat/${id}`}
            className="flex flex-1 items-center justify-center gap-1.5 py-3.5 text-sm text-slate-600 transition hover:bg-white hover:text-brand-700"
          >
            <MessageSquare className="h-4 w-4 shrink-0" />
            文字对话
          </Link>
        </div>
      </Card>
    </div>
  );
}
