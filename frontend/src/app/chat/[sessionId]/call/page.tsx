"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Mic, MicOff, PhoneOff } from "lucide-react";
import { api } from "@/lib/api";
import { cn, getDeviceId } from "@/lib/utils";
import { Alert, Button, Card, Spinner } from "@/components/ui";

export default function ChatCallPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const deviceId = getDeviceId();
  const queryClient = useQueryClient();
  const id = Number(sessionId);

  const [recording, setRecording] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [subtitle, setSubtitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["conversation", id, deviceId],
    queryFn: () => api.getConversation(id, deviceId),
  });

  useEffect(() => {
    const timer = window.setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!data?.messages.length) return;
    const lastAssistant = [...data.messages].reverse().find((m) => m.role === "assistant");
    if (lastAssistant && !subtitle) {
      setSubtitle(lastAssistant.content);
      playAudio(api.getConversationMessageAudioUrl(id, lastAssistant.id, deviceId));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.messages.length]);

  const playAudio = (url: string) => {
    if (!audioRef.current) audioRef.current = new Audio();
    setPlaying(true);
    audioRef.current.src = url;
    audioRef.current.onended = () => setPlaying(false);
    void audioRef.current.play().catch(() => setPlaying(false));
  };

  const startRecording = async () => {
    if (playing || processing || data?.status !== "active") return;
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
        const result = await api.sendVoiceTurn(id, deviceId, blob);
        setSubtitle(`${result.transcript}\n\n— ${result.content}`);
        await refetch();
        queryClient.invalidateQueries({ queryKey: ["conversations", deviceId] });
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
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (isLoading || !data) return <Spinner label="连接通话..." />;

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center gap-6">
      <Card className="w-full space-y-6 p-8 text-center">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">通话中</p>
          <h1 className="mt-2 text-xl font-bold text-slate-900">{data.title}</h1>
          <p className="mt-1 text-sm text-slate-500">{data.role_ai} · {formatTime(elapsed)}</p>
        </div>

        <div className="mx-auto flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-teal-500 text-4xl text-white shadow-lg">
          {data.role_ai.charAt(0)}
        </div>

        <div className="min-h-[5rem] rounded-xl bg-slate-50 px-4 py-3 text-left text-sm leading-relaxed text-slate-700 whitespace-pre-wrap">
          {subtitle || "等待对方发言..."}
        </div>

        {error && <Alert variant="warning">{error}</Alert>}

        {processing && <p className="text-sm text-slate-500">识别与回复中...</p>}
        {playing && <p className="text-sm text-brand-600">对方正在说话...</p>}

        <div className="flex items-center justify-center gap-6">
          <button
            type="button"
            disabled={playing || processing || data.status !== "active"}
            onMouseDown={() => void startRecording()}
            onMouseUp={stopRecording}
            onMouseLeave={() => recording && stopRecording()}
            onTouchStart={() => void startRecording()}
            onTouchEnd={stopRecording}
            className={cn(
              "flex h-16 w-16 items-center justify-center rounded-full transition-all",
              recording ? "bg-red-500 text-white scale-110" : "bg-brand-100 text-brand-700 hover:bg-brand-200",
              (playing || processing) && "opacity-50",
            )}
          >
            {recording ? <MicOff className="h-7 w-7" /> : <Mic className="h-7 w-7" />}
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

        <Link href={`/chat/${id}`}>
          <Button variant="ghost" size="sm" className="w-full">
            切换文字对话
          </Button>
        </Link>
      </Card>
    </div>
  );
}
