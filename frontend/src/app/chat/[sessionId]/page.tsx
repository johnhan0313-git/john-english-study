"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Phone, Send, Square } from "lucide-react";
import { api, ConversationMessage } from "@/lib/api";
import { cn, getDeviceId } from "@/lib/utils";
import { Alert, Badge, Button, Card, Spinner } from "@/components/ui";

export default function ChatSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const router = useRouter();
  const deviceId = getDeviceId();
  const queryClient = useQueryClient();
  const id = Number(sessionId);

  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [showChineseHint, setShowChineseHint] = useState(true);
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof api.endConversation>> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["conversation", id, deviceId],
    queryFn: () => api.getConversation(id, deviceId),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data?.messages, streamContent]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || streaming || data?.status !== "active") return;

    setInput("");
    setStreaming(true);
    setStreamContent("");
    setError(null);

    const optimisticUser: ConversationMessage = {
      id: Date.now(),
      role: "user",
      content: text,
      meta: {},
      created_at: new Date().toISOString(),
    };

    queryClient.setQueryData(["conversation", id, deviceId], (old: typeof data) =>
      old ? { ...old, messages: [...old.messages, optimisticUser] } : old,
    );

    await api.streamConversationMessage(id, deviceId, text, showChineseHint, {
      onToken: (token) => setStreamContent((prev) => prev + token),
      onDone: async () => {
        setStreaming(false);
        setStreamContent("");
        await refetch();
        queryClient.invalidateQueries({ queryKey: ["conversations", deviceId] });
      },
      onError: (message) => {
        setStreaming(false);
        setStreamContent("");
        setError(message);
        refetch();
      },
    });
  };

  const handleEnd = async () => {
    const result = await api.endConversation(id, deviceId);
    setSummary(result);
    await refetch();
    queryClient.invalidateQueries({ queryKey: ["conversations", deviceId] });
  };

  if (isLoading || !data) return <Spinner label="加载对话..." />;

  const usedSet = new Set(data.words_used.map((w) => w.toLowerCase()));

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <Card className="shrink-0 space-y-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold text-slate-900">{data.title}</h1>
            <p className="text-sm text-slate-500">
              你扮演 {data.role_user} · 对方 {data.role_ai} · {data.turn_count} 轮
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.status === "active" && (
              <>
                <Link href={`/chat/${id}/call`}>
                  <Button variant="outline" size="sm">
                    <Phone className="mr-1.5 h-4 w-4" />
                    电话模式
                  </Button>
                </Link>
                <Button variant="outline" size="sm" onClick={() => void handleEnd()}>
                  <Square className="mr-1.5 h-4 w-4" />
                  结束对话
                </Button>
              </>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {data.target_words.map((word) => (
            <Badge key={word} variant={usedSet.has(word.toLowerCase()) ? "success" : "outline"}>
              {word}
            </Badge>
          ))}
        </div>
      </Card>

      {error && <Alert variant="warning">{error}</Alert>}

      <Card className="flex-1 overflow-y-auto space-y-3 p-4">
        {data.messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
                msg.role === "user"
                  ? "bg-hero-gradient text-white"
                  : "border border-surface-border bg-white text-slate-800",
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {streaming && streamContent && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl border border-brand-200 bg-brand-50 px-4 py-2.5 text-sm text-slate-800">
              {streamContent}
              <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-brand-500" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </Card>

      {summary && (
        <Card className="shrink-0 space-y-2 border-emerald-200 bg-emerald-50/80">
          <h3 className="font-semibold text-emerald-900">学习总结</h3>
          <p className="text-sm text-emerald-800">{summary.summary}</p>
          <p className="text-sm text-emerald-700">{summary.vocabulary_feedback}</p>
          {summary.grammar_feedback && <p className="text-sm text-emerald-700">{summary.grammar_feedback}</p>}
          {summary.suggestions.length > 0 && (
            <ul className="list-inside list-disc text-sm text-emerald-700">
              {summary.suggestions.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {data.status === "active" && (
        <Card className="shrink-0 space-y-3">
          <label className="flex items-center gap-2 text-xs text-slate-500">
            <input
              type="checkbox"
              checked={showChineseHint}
              onChange={(e) => setShowChineseHint(e.target.checked)}
            />
            中文提示
          </label>
          <div className="flex gap-2">
            <input
              className="input-field flex-1"
              placeholder="用英文回复..."
              value={input}
              disabled={streaming}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void handleSend();
                }
              }}
            />
            <Button disabled={streaming || !input.trim()} onClick={() => void handleSend()}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      )}

      {data.status === "ended" && !summary && data.summary && (
        <Card className="shrink-0 text-sm text-slate-600">{data.summary}</Card>
      )}
    </div>
  );
}
