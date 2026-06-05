"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Button, Card, Spinner } from "@/components/ui";

function GenerateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const deviceId = getDeviceId();
  const wordIdsParam = searchParams.get("word_ids");
  const initialWordIds = wordIdsParam ? wordIdsParam.split(",").map(Number).filter(Boolean) : [];

  const [level, setLevel] = useState("cet4");
  const [theme, setTheme] = useState("");
  const [scenarioType, setScenarioType] = useState("narrative");
  const [wordCount, setWordCount] = useState(10);

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.generateScenario({
        level,
        theme: theme || undefined,
        word_ids: initialWordIds.length ? initialWordIds : undefined,
        scenario_type: scenarioType,
        device_id: deviceId,
        word_count: wordCount,
      }),
    onSuccess: (data) => router.push(`/scenarios/${data.id}`),
  });

  return (
    <Card className="max-w-xl">
      <h2 className="text-lg font-semibold">配置场景</h2>
      {initialWordIds.length > 0 && (
        <p className="mt-2 text-sm text-primary-600">已选 {initialWordIds.length} 个单词</p>
      )}

      <div className="mt-6 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700">级别</label>
          <div className="mt-2 flex gap-2">
            {["cet4", "cet6"].map((l) => (
              <Button key={l} variant={level === l ? "primary" : "outline"} size="sm" onClick={() => setLevel(l)}>
                {l.toUpperCase()}
              </Button>
            ))}
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">主题</label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="mt-2 w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            <option value="">随机主题</option>
            {groups?.map((g) => (
              <option key={g.slug} value={g.slug}>{g.name_zh} ({g.name_en})</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700">场景类型</label>
          <div className="mt-2 flex gap-2">
            {[
              { id: "narrative", label: "叙事短文" },
              { id: "dialogue", label: "对话场景" },
            ].map((t) => (
              <Button
                key={t.id}
                variant={scenarioType === t.id ? "primary" : "outline"}
                size="sm"
                onClick={() => setScenarioType(t.id)}
              >
                {t.label}
              </Button>
            ))}
          </div>
        </div>

        {!initialWordIds.length && (
          <div>
            <label className="text-sm font-medium text-slate-700">词汇数量: {wordCount}</label>
            <input
              type="range"
              min={5}
              max={15}
              value={wordCount}
              onChange={(e) => setWordCount(Number(e.target.value))}
              className="mt-2 w-full"
            />
          </div>
        )}

        <Button
          className="w-full"
          size="lg"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <>生成中...</>
          ) : (
            <>
              <Sparkles className="mr-2 h-4 w-4" />
              生成场景
            </>
          )}
        </Button>

        {mutation.isError && (
          <p className="text-sm text-red-600">生成失败: {(mutation.error as Error).message}</p>
        )}
      </div>
    </Card>
  );
}

export default function GeneratePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">生成场景</h1>
        <p className="text-slate-600">AI 根据词汇和主题创建沉浸式学习场景</p>
      </div>
      <Suspense fallback={<Spinner />}>
        <GenerateForm />
      </Suspense>
    </div>
  );
}
