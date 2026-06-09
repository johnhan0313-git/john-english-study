"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect } from "react";
import { Mic, MicOff, PhoneOff } from "lucide-react";
import { cn, getDeviceId } from "@/lib/utils";
import { Alert, Button, Card, Spinner } from "@/components/ui";
import { formatCallTime, useVoiceTurn } from "@/hooks/use-voice-turn";
import { api } from "@/lib/api";

export default function ChatCallPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const deviceId = getDeviceId();
  const id = Number(sessionId);

  const { data, isLoading } = useQuery({
    queryKey: ["conversation", id, deviceId],
    queryFn: () => api.getConversation(id, deviceId),
  });

  const voice = useVoiceTurn({
    sessionId: id,
    deviceId,
    enabled: data?.status === "active",
    initialStarted: true,
  });

  const { playOpeningIfNeeded, started } = voice;

  useEffect(() => {
    playOpeningIfNeeded(data?.messages, data?.status ?? "active");
  }, [data?.messages, data?.status, playOpeningIfNeeded, started]);

  if (isLoading || !data) return <Spinner label="连接通话..." />;

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center gap-6">
      <Card className="w-full space-y-6 p-8 text-center">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">通话中</p>
          <h1 className="mt-2 text-xl font-bold text-slate-900">{data.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {data.role_ai} · {formatCallTime(voice.elapsed)}
          </p>
        </div>

        <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-teal-500 text-4xl text-white shadow-lg">
          {data.role_ai.charAt(0)}
        </div>

        <div className="min-h-[5rem] rounded-xl bg-slate-50 px-4 py-3 text-left text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
          {voice.subtitle || "等待对方发言..."}
        </div>

        {voice.error && <Alert variant="warning">{voice.error}</Alert>}

        {voice.processing && <p className="text-sm text-slate-500">识别与回复中...</p>}
        {voice.playing && <p className="text-sm text-brand-600">对方正在说话...</p>}

        <div className="flex items-center justify-center gap-6">
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
              voice.recording ? "bg-red-500 text-white scale-110" : "bg-brand-100 text-brand-700 hover:bg-brand-200",
              (voice.playing || voice.processing) && "opacity-50",
            )}
          >
            {voice.recording ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
          </button>

          <Link href={`/chat/${id}`}>
            <button
              type="button"
              className="flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600 hover:bg-red-200"
            >
              <PhoneOff className="h-6 w-6" />
            </button>
          </Link>
        </div>

        <p className="text-xs text-slate-400">按住麦克风说话，松开后发送</p>

        <Link href={`/chat/${id}/immersive`}>
          <Button variant="outline" size="sm" className="w-full">
            切换沉浸模式
          </Button>
        </Link>

        <Link href={`/chat/${id}`}>
          <Button variant="ghost" size="sm" className="w-full">
            切换文字对话
          </Button>
        </Link>
      </Card>
    </div>
  );
}
