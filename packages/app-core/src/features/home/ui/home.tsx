"use client";

import { useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { ArrowRight, Flame, RefreshCw, Target, Trophy, Zap } from "lucide-react";
import { api } from "@sceneenglish/api-client";
import { Badge, Button, Card, EmptyState, ProgressBar, SectionTitle, Spinner, StatCard } from "../../../app-chrome/ui";
import { useAuth } from "../../auth";
import { dailyKindLabel, homeCopy } from "../model";

const dailyKindVariant: Record<string, "warning" | "brand"> = {
  review: "warning",
  new: "brand",
  challenge: "warning",
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
    <div className="space-y-9">
      <section className="border-b border-surface-border pb-8 pt-3 sm:flex sm:items-end sm:justify-between sm:gap-8 sm:pt-6">
        <div className="max-w-2xl">
          <p className="mb-3 text-sm font-semibold text-brand-700">{homeCopy.heroEyebrow}</p>
          <h1 className="font-display text-3xl font-bold text-slate-950 sm:text-4xl">{homeCopy.heroTitle}</h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-600">{homeCopy.heroDescription}</p>
        </div>
        <div className="mt-5 shrink-0 sm:mt-0">
          {
          isAuthenticated ? (
            <Link href="/chat/new">
              <Button size="lg" className="w-full sm:w-auto">
                <ArrowRight className="mr-2 h-4 w-4" />
                {homeCopy.startChat}
              </Button>
            </Link>
          ) : (
            <Link href="/login?next=/chat/new">
              <Button size="lg" className="w-full sm:w-auto">{homeCopy.loginToStart}</Button>
            </Link>
          )
          }
        </div>
      </section>

      {!isAuthenticated && (
        <Card className="border-brand-100 bg-brand-50/50">
          <p className="text-sm text-slate-700">
            <Link href="/login" className="font-semibold text-brand-700 hover:underline">{homeCopy.login}</Link>
            {" "}{homeCopy.guestHintPrefix}
          </p>
        </Card>
      )}

      {progress && (
        <section>
          <div className="mb-4 flex items-end justify-between gap-3">
            <h2 className="text-lg font-bold text-slate-900">{homeCopy.progressTitle}</h2>
            <Link href="/progress" className="text-sm font-medium text-brand-600 hover:text-brand-700">
              {homeCopy.progressDetail}
              <ArrowRight className="ml-0.5 inline h-4 w-4" />
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label={homeCopy.streakLabel} value={progress.current_streak} suffix={homeCopy.streakSuffix} icon={Flame} tone="amber" />
          <StatCard label={homeCopy.dueReviewLabel} value={progress.due_review} icon={Zap} tone="violet" />
          <StatCard label={homeCopy.masteredLabel} value={progress.mastered_words} icon={Trophy} tone="emerald" />
          <StatCard label={homeCopy.masteryRateLabel} value={`${progress.mastery_rate}`} suffix="%" icon={Target} tone="brand">
            <ProgressBar value={progress.mastery_rate} />
          </StatCard>
          </div>
        </section>
      )}

      <section>
        <SectionTitle
          title={homeCopy.dailySectionTitle}
          action={
            isAuthenticated ? (
              <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
                <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
                {homeCopy.refresh}
              </Button>
            ) : undefined
          }
        />

        {!isAuthenticated ? (
          <EmptyState
            title={homeCopy.loginForDailyTitle}
            description={homeCopy.loginForDailyDescription}
            action={
              <Link href="/login?next=/">
                <Button>{homeCopy.login}</Button>
              </Link>
            }
          />
        ) : isLoading ? (
          <Spinner label={homeCopy.loadingDaily} />
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
                    {homeCopy.startLearning}
                    <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title={homeCopy.noDailyTitle}
            description={homeCopy.noDailyDescription}
            action={
              <Link href="/activity?tab=scenarios">
                <Button>{homeCopy.goToScenarios}</Button>
              </Link>
            }
          />
        )}
      </section>

    </div>
  );
}
