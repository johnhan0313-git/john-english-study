"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Search, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId, cn } from "@/lib/utils";
import { Badge, Button, Card, Input, PageHeader, Spinner } from "@/components/ui";

export default function WordsPage() {
  const deviceId = getDeviceId();
  const [page, setPage] = useState(1);
  const [level, setLevel] = useState<string>("");
  const [theme, setTheme] = useState<string>("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number[]>([]);

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["words", page, level, theme, search, deviceId],
    queryFn: () =>
      api.getWords({
        page,
        page_size: 30,
        device_id: deviceId,
        ...(level && { level }),
        ...(theme && { theme }),
        ...(search && { search }),
      }),
  });

  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 15 ? [...prev, id] : prev,
    );
  };

  const familiarityDot = (f: number | null) => {
    if (f === null || f === 0) return "bg-slate-300";
    if (f <= 2) return "bg-amber-400";
    if (f <= 4) return "bg-brand-400";
    return "bg-emerald-500";
  };

  return (
    <div className="animate-fade-in space-y-6">
      <PageHeader
        badge="词汇库"
        title="CET-4/6 词库"
        description={`共 ${data?.total ?? "..."} 词 · 点击选词可批量生成场景`}
        action={
          selected.length > 0 ? (
            <Link href={`/generate?word_ids=${selected.join(",")}`}>
              <Button>
                <Sparkles className="mr-2 h-4 w-4" />
                生成场景 ({selected.length})
              </Button>
            </Link>
          ) : undefined
        }
      />

      <Card className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="搜索单词..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-10"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {["", "cet4", "cet6"].map((l) => (
            <button
              key={l || "all"}
              type="button"
              className={level === l ? "chip-active" : "chip-inactive"}
              onClick={() => { setLevel(l); setPage(1); }}
            >
              {l === "" ? "全部级别" : l.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={theme === "" ? "chip-active" : "chip-inactive"} onClick={() => { setTheme(""); setPage(1); }}>
            全部主题
          </button>
          {groups?.map((g) => (
            <button
              key={g.slug}
              type="button"
              className={theme === g.slug ? "chip-active" : "chip-inactive"}
              onClick={() => { setTheme(g.slug); setPage(1); }}
            >
              {g.name_zh}
            </button>
          ))}
        </div>
      </Card>

      {isLoading ? (
        <Spinner label="加载词库..." />
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((w) => (
              <Card
                key={w.id}
                hover
                className={cn(
                  "cursor-pointer",
                  selected.includes(w.id) && "ring-2 ring-brand-500 ring-offset-2",
                )}
                onClick={() => toggleSelect(w.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={cn("h-2 w-2 shrink-0 rounded-full", familiarityDot(w.familiarity))} />
                    <span className="text-lg font-bold text-slate-900">{w.lemma}</span>
                    {w.pos && <span className="text-xs text-slate-400">{w.pos}</span>}
                  </div>
                  <Badge variant={w.level === "cet6" ? "purple" : "brand"}>{w.level}</Badge>
                </div>
                <p className="mt-2 line-clamp-2 text-sm text-slate-600">{w.definitions[0]}</p>
                {w.familiarity != null && w.familiarity > 0 && (
                  <div className="mt-3 flex gap-1">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div
                        key={i}
                        className={cn("h-1 flex-1 rounded-full", i < w.familiarity! ? "bg-brand-400" : "bg-slate-100")}
                      />
                    ))}
                  </div>
                )}
              </Card>
            ))}
          </div>

          <div className="flex items-center justify-center gap-3 pt-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <span className="rounded-full bg-white/80 px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm">
              {page} / {Math.ceil((data?.total || 0) / 30) || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= Math.ceil((data?.total || 0) / 30)}
              onClick={() => setPage((p) => p + 1)}
            >
              下一页
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
