"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, Flame, RefreshCw, Target, Trophy, Zap } from "lucide-react";
import { api } from "@/lib/api";
import { Badge, Button, Card, EmptyState, PageHeader, ProgressBar, SectionTitle, Spinner, StatCard } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";

const dailyKindLabel: Record<string, string> = {
  review: "复习场景",
  new: "新词场景",
  challenge: "挑战场景",
};

const dailyKindVariant: Record<string, "warning" | "brand" | "purple"> = {
  review: "warning",
  new: "brand",
  challenge: "purple",
};

export default function HomePage() {
  const { isAuthenticated } = useAuth();

  const { data: progress } = useQuery({
    queryKey: ["progress"],
    queryFn: () => api.getProgress(),
    enabled: isAuthenticated,
  });

  const { data: daily, isLoading, refetch, isFetching } = useQuery({
    queryKey: ["daily"],
    queryFn: () => api.getDailyScenarios(),
    enabled: isAuthenticated,
  });

  return (
    <div className="space-y-10">
      <PageHeader
        badge="每日学习"
        title="沉浸式场景学英语"
        description="把 CET-4/6 词汇放进真实语境，听说读写一站练完"
        action={
          isAuthenticated ? (
            <Link href="/chat/new">
              <Button size="lg">
                <ArrowRight className="mr-2 h-4 w-4" />
                开始对话
              </Button>
            </Link>
          ) : (
            <Link href="/login?next=/chat/new">
              <Button size="lg">登录开始</Button>
            </Link>
          )
        }
      />

      {!isAuthenticated && (
        <Card className="border-brand-100 bg-brand-50/50">
          <p className="text-sm text-slate-700">
            <Link href="/login" className="font-semibold text-brand-700 hover:underline">登录</Link>
            {" "}后可查看学习进度、今日场景与对话记录。词库与参考内容可匿名浏览。
          </p>
        </Card>
      )}

      {progress && (
        <section>
          <div className="mb-4 flex items-end justify-between gap-3">
            <h2 className="text-lg font-bold text-slate-900">学习进度</h2>
            <Link href="/progress" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              查看详情
              <ArrowRight className="ml-0.5 inline h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="连续学习" value={progress.current_streak} suffix="天" icon={Flame} tone="amber" />
          <StatCard label="待复习" value={progress.due_review} icon={Zap} tone="violet" />
          <StatCard label="已掌握" value={progress.mastered_words} icon={Trophy} tone="emerald" />
          <StatCard label="掌握率" value={`${progress.mastery_rate}`} suffix="%" icon={Target} tone="brand">
            <ProgressBar value={progress.mastery_rate} />
          </StatCard>
          </div>
        </section>
      )}

      <section>
        <SectionTitle
          title="今日场景"
          action={
            isAuthenticated ? (
              <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
                <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
                刷新
              </Button>
            ) : undefined
          }
        />

        {!isAuthenticated ? (
          <EmptyState
            title="登录查看今日场景"
            description="每日场景会根据你的学习进度自动生成"
            action={
              <Link href="/login?next=/">
                <Button>登录</Button>
              </Link>
            }
          />
        ) : isLoading ? (
          <Spinner label="正在加载今日场景..." />
        ) : daily?.items.length ? (
          <div className="grid gap-4 md:grid-cols-3">
            {daily.items.map((s) => (
              <Link key={s.id} href={`/scenarios/${s.id}`} className="block">
                <Card hover className="group h-full">
                  <div className="flex items-start justify-between gap-2">
                    <Badge variant={dailyKindVariant[s.daily_kind || ""] || "outline"}>
                      {dailyKindLabel[s.daily_kind || ""] || s.theme}
                    </Badge>
                    <Badge variant="outline">{s.level.toUpperCase()}</Badge>
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-900 group-hover:text-brand-700 transition-colors">
                    {s.title}
                  </h3>
                  <p className="mt-2 text-sm text-slate-500">{s.word_count} 个目标词 · {s.scenario_type}</p>
                  <div className="mt-5 flex items-center text-sm font-semibold text-brand-600">
                    开始学习
                    <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="还没有今日场景"
            description="点击下方按钮，AI 会根据你的学习进度生成专属场景"
            action={
              <Link href="/activity?tab=scenarios">
                <Button>去场景页</Button>
              </Link>
            }
          />
        )}
      </section>

    </div>
  );
}
