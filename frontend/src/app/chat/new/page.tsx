"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Loader2, MessageCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Button, Card, PageHeader, Select, Spinner } from "@/components/ui";

function NewChatForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const scenarioId = searchParams.get("scenario_id");

  const [level, setLevel] = useState("cet4");
  const [theme, setTheme] = useState("");
  const [wordCount, setWordCount] = useState(8);
  const [showChineseHint, setShowChineseHint] = useState(true);

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.createConversation({
        level,
        theme: theme || undefined,
        word_count: wordCount,
        show_chinese_hint: showChineseHint,
        ...(scenarioId ? { scenario_id: Number(scenarioId) } : {}),
      }),
    onSuccess: (data) => router.push(`/chat/${data.id}`),
  });

  return (
    <Card className="mx-auto max-w-xl space-y-6">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
          <MessageCircle className="h-5 w-5" />
        </div>
        <div>
          <h2 className="font-bold text-slate-900">新建 1v1 对话</h2>
          {scenarioId && <p className="text-sm text-brand-600">基于场景 #{scenarioId}</p>}
        </div>
      </div>

      {!scenarioId && (
        <>
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">级别</label>
            <div className="flex gap-2">
              {["cet4", "cet6"].map((l) => (
                <button
                  key={l}
                  type="button"
                  className={level === l ? "chip-active" : "chip-inactive"}
                  onClick={() => setLevel(l)}
                >
                  {l.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">主题</label>
            <Select value={theme} onChange={(e) => setTheme(e.target.value)}>
              <option value="">日常对话</option>
              {groups?.map((g) => (
                <option key={g.slug} value={g.slug}>{g.name_zh}</option>
              ))}
            </Select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">目标词数量</label>
            <Select value={wordCount} onChange={(e) => setWordCount(Number(e.target.value))}>
              {[5, 8, 10, 12, 15].map((n) => (
                <option key={n} value={n}>{n} 词</option>
              ))}
            </Select>
          </div>
        </>
      )}

      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={showChineseHint}
          onChange={(e) => setShowChineseHint(e.target.checked)}
          className="rounded border-surface-border"
        />
        AI 附带中文释义
      </label>

      <Button className="w-full" disabled={mutation.isPending} onClick={() => mutation.mutate()}>
        {mutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            创建中...
          </>
        ) : (
          "开始对话"
        )}
      </Button>
    </Card>
  );
}

export default function NewChatPage() {
  return (
    <div className="space-y-6">
      <PageHeader badge="1v1 对话" title="新建对话" description="选择场景参数，与 AI 角色开始沉浸式练习" />
      <Suspense fallback={<Spinner label="加载..." />}>
        <NewChatForm />
      </Suspense>
    </div>
  );
}
