"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Calendar, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { RequireAuth } from "@/components/auth/require-auth";
import { Badge, Card, EmptyState, PageHeader, Spinner } from "@/components/ui";

function ScenariosListContent() {
  const { data, isLoading } = useQuery({
    queryKey: ["scenarios"],
    queryFn: () => api.listScenarios(),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        badge="学习记录"
        title="场景列表"
        description="回顾历史学习场景，继续未完成的练习"
      />

      {isLoading ? (
        <Spinner label="加载场景..." />
      ) : data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((s) => (
            <Link key={s.id} href={`/scenarios/${s.id}`} className="block">
              <Card hover className="group">
                <div className="flex items-center gap-4">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                    <Calendar className="h-5 w-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-bold text-slate-900 group-hover:text-brand-700">{s.title}</h3>
                    <p className="mt-0.5 text-sm text-slate-500">
                      {s.theme} · {s.word_count} 词 · {new Date(s.created_at).toLocaleDateString("zh-CN")}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {s.is_daily && <Badge variant="success">每日</Badge>}
                    <Badge variant="outline">{s.level.toUpperCase()}</Badge>
                    <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-brand-500 transition-colors" />
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState title="暂无场景" description="去首页获取今日场景，或手动生成一个新场景" />
      )}
    </div>
  );
}

export default function ScenariosPage() {
  return (
    <RequireAuth>
      <ScenariosListContent />
    </RequireAuth>
  );
}
