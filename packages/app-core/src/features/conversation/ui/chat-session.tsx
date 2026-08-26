"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useParams } from "../../../platform/context";
import { useEffect, useRef, useState } from "react";
import { Loader2, Phone, Send, Sparkles, Square } from "lucide-react";
import { api, ConversationMessage } from "@sceneenglish/api-client";
import { getConversationChineseHint } from "@sceneenglish/api-client";
import { cn } from "../../../app-chrome/utils";
import { Alert, Badge, Button, Card, Spinner } from "../../../app-chrome/ui";

export default function ChatSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const queryClient = useQueryClient();
  const id = Number(sessionId);

  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [showChineseHint, setShowChineseHint] = useState(true);
  const [hintSaving, setHintSaving] = useState(false);
  const [summary, setSummary] = useState<Awaited<ReturnType<typeof api.endConversation>> | null>(null);
  const [ending, setEnding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => api.getConversation(id),
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data?.messages, streamContent, ending]);

  useEffect(() => {
    if (!data) return;
    setShowChineseHint(getConversationChineseHint(data.scene_brief));
  }, [data]);

  const handleChineseHintChange = async (checked: boolean) => {
    setShowChineseHint(checked);
    setHintSaving(true);
    setError(null);
    try {
      const updated = await api.updateConversationSettings(id, { show_chinese_hint: checked });
      queryClient.setQueryData(["conversation", id], updated);
    } catch (e) {
      setShowChineseHint(!checked);
      setError(e instanceof Error ? e.message : "更新设置失败");
    } finally {
      setHintSaving(false);
    }
  };

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

    queryClient.setQueryData(["conversation", id], (old: typeof data) =>
      old ? { ...old, messages: [...old.messages, optimisticUser] } : old,
    );

    await api.streamConversationMessage(id, text, showChineseHint, {
      onToken: (token) => setStreamContent((prev) => prev + token),
      onDone: async () => {
        setStreaming(false);
        setStreamContent("");
        await refetch();
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
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
    if (ending) return;
    setEnding(true);
    setError(null);
    try {
      const result = await api.endConversation(id);
      setSummary(result);
      await refetch();
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    } catch (e) {
      setError(e instanceof Error ? e.message : "生成总结失败，请重试");
    } finally {
      setEnding(false);
    }
  };

  if (isLoading || !data) return <Spinner label="加载对话..." />;

  const usedSet = new Set(data.words_used.map((w) => w.toLowerCase()));

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-4">
      <Card className="shrink-0 space-y-3">
        <div className="space-y-3">
          <div>
            <h1 className="text-lg font-bold text-slate-900">{data.title}</h1>
            <p className="text-sm text-slate-500">
              你扮演 {data.role_user} · 对方 {data.role_ai} · {data.turn_count} 轮
            </p>
          </div>

          {data.status === "active" && (
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex overflow-hidden rounded-xl border border-surface-border/80 bg-slate-50/50">
                <Link
                  href={`/chat/${id}/call`}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-white hover:text-brand-700",
                    (ending || streaming) && "pointer-events-none opacity-50",
                  )}
                >
                  <Phone className="h-4 w-4 shrink-0" />
                  电话模式
                </Link>
                <div className="w-px bg-surface-border/60" />
                <Link
                  href={`/chat/${id}/immersive`}
                  className={cn(
                    "flex flex-1 items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-white hover:text-brand-700",
                    (ending || streaming) && "pointer-events-none opacity-50",
                  )}
                >
                  <Sparkles className="h-4 w-4 shrink-0" />
                  沉浸模式
                </Link>
              </div>

              <button
                type="button"
                disabled={ending || streaming}
                onClick={() => void handleEnd()}
                className="inline-flex items-center justify-center gap-1.5 self-end text-sm font-medium text-red-600 transition hover:text-red-700 disabled:opacity-50 sm:self-auto"
              >
                {ending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    生成总结中...
                  </>
                ) : (
                  <>
                    <Square className="h-4 w-4" />
                    结束对话
                  </>
                )}
              </button>
            </div>
          )}
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

      <Card className={cn("relative flex-1 overflow-y-auto space-y-3 p-4", ending && "opacity-60")}>
        {data.messages.map((msg) => (
          <div
            key={msg.id}
            className={cn("flex", msg.role === "user" ? "justify-end" : "justify-start")}
          >
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-4 py-3 reading-text",
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

      {ending && (
        <Card className="shrink-0 border-brand-200 bg-brand-50/90">
          <div className="flex items-start gap-4">
            <div className="relative mt-0.5 h-10 w-10 shrink-0">
              <div className="absolute inset-0 animate-spin rounded-full border-2 border-brand-100 border-t-brand-600" />
              <div className="absolute inset-1 animate-pulse rounded-full bg-white/80" />
            </div>
            <div className="min-w-0 space-y-1">
              <p className="font-medium text-brand-900">正在生成学习总结</p>
              <p className="text-sm text-brand-700">AI 正在回顾本轮对话，分析用词与表达，请稍候…</p>
              <p className="text-xs text-brand-600/80">通常需要 5–15 秒，请勿关闭页面</p>
            </div>
          </div>
        </Card>
      )}

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

      {data.status === "active" && !ending && (
        <Card className="shrink-0 space-y-3">
          <div className="flex items-center justify-between gap-3 rounded-xl border border-surface-border/60 bg-slate-50/70 px-3 py-2.5">
            <div className="min-w-0 text-left">
              <p className="text-sm font-medium text-slate-700">AI 附带中文释义</p>
              <p className="text-xs text-slate-500">开启后英文回复末尾会加括号中文，仅影响后续消息</p>
            </div>
            <label className="relative inline-flex shrink-0 cursor-pointer items-center">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={showChineseHint}
                disabled={hintSaving || streaming}
                onChange={(e) => void handleChineseHintChange(e.target.checked)}
              />
              <span className="h-6 w-11 rounded-full bg-slate-200 transition peer-checked:bg-brand-500 peer-disabled:opacity-50" />
              <span className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-white shadow transition peer-checked:translate-x-5" />
            </label>
          </div>
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
