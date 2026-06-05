"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, Flame, RefreshCw, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Button, Card, ProgressBar, Spinner } from "@/components/ui";

const dailyKindLabel: Record<string, string> = {
  review: "复习场景",
  new: "新词场景",
  challenge: "挑战场景",
};

export default function HomePage() {
  const deviceId = getDeviceId();

  const { data: progress } = useQuery({
    queryKey: ["progress", deviceId],
    queryFn: () => api.getProgress(deviceId),
  });

  const { data: daily, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["daily", deviceId],
    queryFn: () => api.getDailyScenarios(deviceId),
  });

  return (
    <div className="space-y-8">
      <section>
        <h1 className="text-3xl font-bold text-slate-900">今日学习</h1>
        <p className="mt-2 text-slate-600">
          场景化学习 CET-4/6 词汇，听说读写一站练习
        </p>
      </section>

      {progress && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <Flame className="h-4 w-4 text-orange-500" />
              连续学习
            </div>
            <p className="mt-2 text-2xl font-bold">{progress.current_streak} 天</p>
          </Card>
          <Card>
            <div className="text-sm text-slate-500">待复习</div>
            <p className="mt-2 text-2xl font-bold text-amber-600">{progress.due_review}</p>
          </Card>
          <Card>
            <div className="text-sm text-slate-500">已掌握</div>
            <p className="mt-2 text-2xl font-bold text-green-600">{progress.mastered_words}</p>
          </Card>
          <Card>
            <div className="text-sm text-slate-500">掌握率</div>
            <p className="mt-2 text-2xl font-bold">{progress.mastery_rate}%</p>
            <div className="mt-2">
              <ProgressBar value={progress.mastery_rate} />
            </div>
          </Card>
        </div>
      )}

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">今日场景</h2>
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-1 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            刷新
          </Button>
        </div>

        {isLoading ? (
          <Spinner />
        ) : daily?.items.length ? (
          <div className="grid gap-4 md:grid-cols-3">
            {daily.items.map((s) => (
              <Link key={s.id} href={`/scenarios/${s.id}`}>
                <Card className="h-full transition-shadow hover:shadow-md">
                  <div className="flex items-start justify-between">
                    <Badge variant={s.daily_kind === "challenge" ? "purple" : "default"}>
                      {dailyKindLabel[s.daily_kind || ""] || s.theme}
                    </Badge>
                    <Badge>{s.level.toUpperCase()}</Badge>
                  </div>
                  <h3 className="mt-3 font-semibold">{s.title}</h3>
                  <p className="mt-1 text-sm text-slate-500">{s.word_count} 个目标词</p>
                  <div className="mt-4 flex items-center text-sm text-primary-600">
                    开始学习 <ArrowRight className="ml-1 h-4 w-4" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card className="text-center">
            <p className="text-slate-600">暂无今日场景，点击下方按钮生成</p>
          </Card>
        )}
      </section>

      <Card className="flex flex-col items-start gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold">手动生成场景</h3>
          <p className="text-sm text-slate-500">选择主题和词汇，AI 为你定制学习场景</p>
        </div>
        <Link href="/generate">
          <Button>
            <Sparkles className="mr-2 h-4 w-4" />
            生成场景
          </Button>
        </Link>
      </Card>
    </div>
  );
}
