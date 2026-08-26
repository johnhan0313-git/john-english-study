"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { BookText, ChevronRight, Search, X } from "lucide-react";
import { api, GrammarBrief, GrammarDetail } from "@sceneenglish/api-client";
import { cn } from "../../../app-chrome/utils";
import { MobileDetailSheet } from "./mobile-detail-sheet";
import { Badge, Card, Input, Spinner, StatCard } from "../../../app-chrome/ui";

const LEVEL_LABEL: Record<string, string> = {
  cet4: "四级",
  cet6: "六级",
  both: "四/六级",
};

function levelBadge(level: string) {
  if (level === "cet6") return "purple" as const;
  if (level === "both") return "brand" as const;
  return "success" as const;
}

function GrammarItem({
  item,
  active,
  onClick,
}: {
  item: GrammarBrief;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition-all",
        active
          ? "border-brand-300 bg-brand-50/80 ring-2 ring-brand-200"
          : "border-surface-border bg-white/80 hover:border-brand-200 hover:bg-brand-50/40",
      )}
    >
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-semibold text-slate-900">{item.title}</span>
          <Badge variant={levelBadge(item.level)}>{LEVEL_LABEL[item.level] ?? item.level}</Badge>
        </div>
        <p className="mt-1 line-clamp-2 text-sm text-slate-500">{item.summary}</p>
      </div>
      <ChevronRight className="h-4 w-4 shrink-0 text-slate-400" />
    </button>
  );
}

function GrammarDetailPanel({ detail, onClose }: { detail: GrammarDetail; onClose: () => void }) {
  return (
    <Card glass={false} className="space-y-5 border-0 bg-transparent p-0 shadow-none lg:glass-card lg:sticky-below-header lg:border lg:bg-white/80 lg:p-5 lg:shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={levelBadge(detail.level)}>{LEVEL_LABEL[detail.level] ?? detail.level}</Badge>
            <Badge variant="outline">{detail.category}</Badge>
          </div>
          <h2 className="mt-2 text-xl font-bold text-slate-900">{detail.title}</h2>
          <p className="mt-1 text-sm text-slate-600">{detail.summary}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {detail.structure && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-700">结构</h3>
          <p className="rounded-xl bg-brand-50 px-4 py-3 font-mono text-sm text-brand-900">{detail.structure}</p>
        </div>
      )}

      {detail.rules.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-700">要点</h3>
          <ul className="space-y-2">
            {detail.rules.map((rule) => (
              <li key={rule} className="flex gap-2 text-sm text-slate-700">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                {rule}
              </li>
            ))}
          </ul>
        </div>
      )}

      {detail.examples.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-700">例句</h3>
          <div className="space-y-3">
            {detail.examples.map((ex) => (
              <div key={ex.en} className="rounded-xl border border-surface-border bg-white px-4 py-3">
                <p className="text-sm font-medium text-slate-900">{ex.en}</p>
                <p className="mt-1 text-sm text-slate-500">{ex.zh}</p>
                {ex.note && <p className="mt-1 text-xs text-brand-600">{ex.note}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {detail.tips && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/80 px-4 py-3 text-sm text-amber-900">
          <span className="font-semibold">提示：</span>
          {detail.tips}
        </div>
      )}
    </Card>
  );
}

export default function GrammarPage() {
  const [search, setSearch] = useState("");
  const [level, setLevel] = useState("");
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["grammar", level, search],
    queryFn: () => api.getGrammar({ ...(level && { level }), ...(search && { search }) }),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["grammar-detail", selectedSlug],
    queryFn: () => api.getGrammarPoint(selectedSlug!),
    enabled: selectedSlug !== null,
  });

  const cet4Count = data?.items.filter((i) => i.level === "cet4" || i.level === "both").length ?? 0;
  const cet6Count = data?.items.filter((i) => i.level === "cet6" || i.level === "both").length ?? 0;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="语法点" value={data?.total ?? "—"} icon={BookText} tone="brand" />
        <StatCard label="四级相关" value={cet4Count} icon={BookText} tone="emerald" />
        <StatCard label="六级相关" value={cet6Count} icon={BookText} tone="violet" />
      </div>

      <Card className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="搜索语法标题或摘要..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { id: "", label: "全部" },
            { id: "cet4", label: "四级" },
            { id: "cet6", label: "六级" },
          ].map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setLevel(opt.id)}
              className={cn(
                "rounded-full px-3 py-1.5 text-xs font-semibold transition-all",
                level === opt.id ? "bg-hero-gradient text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </Card>

      {isLoading ? (
        <Spinner label="加载语法..." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
          <div className="space-y-8">
            {data?.groups.map((group) => (
              <section key={group.category}>
                <div className="mb-4 flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900">{group.category_zh}</h2>
                  <Badge variant="brand">{group.count}</Badge>
                </div>
                <div className="space-y-2">
                  {group.items.map((item) => (
                    <GrammarItem
                      key={item.slug}
                      item={item}
                      active={selectedSlug === item.slug}
                      onClick={() => setSelectedSlug(item.slug)}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>

          <aside className="hidden lg:block">
            {selectedSlug === null ? (
              <Card className="sticky-below-header text-center text-sm text-slate-500">
                <BookText className="mx-auto mb-3 h-8 w-8 text-brand-300" />
                点击左侧语法点查看结构与例句
              </Card>
            ) : detailLoading ? (
              <Spinner label="加载详情..." />
            ) : detail ? (
              <GrammarDetailPanel detail={detail} onClose={() => setSelectedSlug(null)} />
            ) : null}
          </aside>
        </div>
      )}

      <MobileDetailSheet open={selectedSlug !== null} onClose={() => setSelectedSlug(null)}>
        {detailLoading ? (
          <Spinner label="加载详情..." />
        ) : detail ? (
          <GrammarDetailPanel detail={detail} onClose={() => setSelectedSlug(null)} />
        ) : null}
      </MobileDetailSheet>
    </div>
  );
}
