"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Card, ProgressBar, Spinner } from "@/components/ui";

export default function ProgressPage() {
  const deviceId = getDeviceId();
  const { data, isLoading } = useQuery({
    queryKey: ["progress", deviceId],
    queryFn: () => api.getProgress(deviceId),
  });

  if (isLoading) return <Spinner />;

  const stats = [
    { label: "词汇总量", value: data?.total_words, color: "text-slate-900" },
    { label: "已学习", value: data?.learned_words, color: "text-blue-600" },
    { label: "已掌握", value: data?.mastered_words, color: "text-green-600" },
    { label: "待复习", value: data?.due_review, color: "text-amber-600" },
    { label: "完成场景", value: data?.scenarios_completed, color: "text-purple-600" },
    { label: "连续天数", value: data?.current_streak, color: "text-orange-600" },
    { label: "最长连续", value: data?.longest_streak, color: "text-orange-500" },
    { label: "完成练习", value: data?.exercises_completed, color: "text-primary-600" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">学习进度</h1>
        <p className="text-slate-600">追踪你的 CET-4/6 学习成果</p>
      </div>

      <Card>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-500">总体掌握率</p>
            <p className="text-4xl font-bold text-primary-600">{data?.mastery_rate ?? 0}%</p>
          </div>
          <div className="w-48">
            <ProgressBar value={data?.mastery_rate ?? 0} />
          </div>
        </div>
      </Card>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label}>
            <p className="text-sm text-slate-500">{s.label}</p>
            <p className={`mt-2 text-2xl font-bold ${s.color}`}>{s.value ?? 0}</p>
          </Card>
        ))}
      </div>

      <Card>
        <h2 className="font-semibold">SRS 间隔重复说明</h2>
        <p className="mt-2 text-sm text-slate-600">
          答对题目后，词汇熟悉度提升，复习间隔依次延长：1天 → 3天 → 7天 → 14天 → 30天。
          答错则重置。每日场景会根据 SRS 算法自动选取待复习词和新词。
        </p>
      </Card>
    </div>
  );
}
