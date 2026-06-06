"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Sparkles, Wand2 } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Alert, Button, Card, PageHeader, Select, Spinner } from "@/components/ui";

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
    <div className="grid gap-6 lg:grid-cols-5">
      <Card className="lg:col-span-3 space-y-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
            <Wand2 className="h-5 w-5" />
          </div>
          <div>
            <h2 className="font-bold text-slate-900">场景配置</h2>
            {initialWordIds.length > 0 && (
              <p className="text-sm text-brand-600">已预选 {initialWordIds.length} 个单词</p>
            )}
          </div>
        </div>

        <div className="space-y-5">
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
              <option value="">随机主题</option>
              {groups?.map((g) => (
                <option key={g.slug} value={g.slug}>{g.name_zh} ({g.name_en})</option>
              ))}
            </Select>
          </div>

          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">场景类型</label>
            <div className="flex gap-2">
              {[
                { id: "narrative", label: "叙事短文" },
                { id: "dialogue", label: "对话场景" },
              ].map((t) => (
                <button
                  key={t.id}
                  type="button"
                  className={scenarioType === t.id ? "chip-active" : "chip-inactive"}
                  onClick={() => setScenarioType(t.id)}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {!initialWordIds.length && (
            <div>
              <label className="mb-2 flex justify-between text-sm font-semibold text-slate-700">
                <span>词汇数量</span>
                <span className="text-brand-600">{wordCount}</span>
              </label>
              <input
                type="range"
                min={5}
                max={15}
                value={wordCount}
                onChange={(e) => setWordCount(Number(e.target.value))}
                className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-brand-600"
              />
            </div>
          )}

          <Button className="w-full" size="lg" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                AI 生成中...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                生成场景
              </>
            )}
          </Button>

          {mutation.isError && (
            <Alert variant="warning">生成失败: {(mutation.error as Error).message}</Alert>
          )}
        </div>
      </Card>

      <Card className="lg:col-span-2 h-fit border-brand-100 bg-gradient-to-b from-brand-50/50 to-white">
        <h3 className="font-bold text-slate-900">生成说明</h3>
        <ul className="mt-4 space-y-3 text-sm text-slate-600">
          <li className="flex gap-2"><span className="text-brand-500">1.</span>AI 根据词汇编写英文场景短文</li>
          <li className="flex gap-2"><span className="text-brand-500">2.</span>自动生成 5 道单选 + 3 道填空</li>
          <li className="flex gap-2"><span className="text-brand-500">3.</span>支持阅读、听力、口语、写作练习</li>
        </ul>
        <p className="mt-4 text-xs text-slate-400">通常需要 10–20 秒，请耐心等待</p>
      </Card>
    </div>
  );
}

export default function GeneratePage() {
  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        badge="AI 驱动"
        title="生成场景"
        description="选择级别、主题和类型，AI 为你定制沉浸式学习材料"
      />
      <Suspense fallback={<Spinner label="加载配置..." />}>
        <GenerateForm />
      </Suspense>
    </div>
  );
}
