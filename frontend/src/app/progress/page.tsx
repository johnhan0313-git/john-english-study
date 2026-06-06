"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  Brain,
  Flame,
  Layers,
  ListChecks,
  Target,
  TrendingUp,
  Trophy,
} from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Card, PageHeader, ProgressBar, Spinner, StatCard } from "@/components/ui";

export default function ProgressPage() {
  const deviceId = getDeviceId();
  const { data, isLoading } = useQuery({
    queryKey: ["progress", deviceId],
    queryFn: () => api.getProgress(deviceId),
  });

  if (isLoading) return <Spinner label="加载进度..." />;

  return (
    <div className="animate-fade-in space-y-8">
      <PageHeader
        badge="学习数据"
        title="学习进度"
        description="追踪词汇掌握、场景完成与复习节奏"
      />

      <Card className="relative overflow-hidden border-brand-100 bg-gradient-to-br from-brand-600 to-brand-700 p-6 text-white">
        <div className="absolute -right-6 -top-6 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-brand-100">总体掌握率</p>
            <p className="mt-1 text-5xl font-bold tracking-tight">{data?.mastery_rate ?? 0}%</p>
            <p className="mt-2 text-sm text-brand-100">
              已掌握 {data?.mastered_words ?? 0} / {data?.total_words ?? 0} 词
            </p>
          </div>
          <div className="w-full sm:w-56">
            <ProgressBar value={data?.mastery_rate ?? 0} className="bg-white/20 [&>div]:bg-white" />
          </div>
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="词汇总量" value={data?.total_words ?? 0} icon={BookOpen} tone="brand" />
        <StatCard label="已学习" value={data?.learned_words ?? 0} icon={Brain} tone="violet" />
        <StatCard label="已掌握" value={data?.mastered_words ?? 0} icon={Trophy} tone="emerald" />
        <StatCard label="待复习" value={data?.due_review ?? 0} icon={Target} tone="amber" />
        <StatCard label="完成场景" value={data?.scenarios_completed ?? 0} icon={Layers} tone="brand" />
        <StatCard label="连续天数" value={data?.current_streak ?? 0} suffix="天" icon={Flame} tone="amber" />
        <StatCard label="最长连续" value={data?.longest_streak ?? 0} suffix="天" icon={TrendingUp} tone="emerald" />
        <StatCard label="完成练习" value={data?.exercises_completed ?? 0} icon={ListChecks} tone="violet" />
      </div>

      <Card>
        <h2 className="font-bold text-slate-900">SRS 间隔重复</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          答对后熟悉度提升，复习间隔延长：1 → 3 → 7 → 14 → 30 天；答错则重置。
          每日场景按 70% 到期复习词 + 30% 新词自动选词。
        </p>
      </Card>
    </div>
  );
}
