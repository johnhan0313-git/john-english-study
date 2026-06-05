"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Button, Card, Spinner } from "@/components/ui";

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

  const familiarityColor = (f: number | null) => {
    if (f === null || f === 0) return "bg-slate-100";
    if (f <= 2) return "bg-amber-100";
    if (f <= 4) return "bg-blue-100";
    return "bg-green-100";
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold">词库</h1>
          <p className="text-slate-600">CET-4/6 词汇，共 {data?.total ?? "..."} 词</p>
        </div>
        {selected.length > 0 && (
          <Link href={`/generate?word_ids=${selected.join(",")}`}>
            <Button>用选中 {selected.length} 词生成场景</Button>
          </Link>
        )}
      </div>

      <div className="flex flex-wrap gap-2">
        {["", "cet4", "cet6"].map((l) => (
          <Button
            key={l || "all"}
            variant={level === l ? "primary" : "outline"}
            size="sm"
            onClick={() => { setLevel(l); setPage(1); }}
          >
            {l === "" ? "全部" : l.toUpperCase()}
          </Button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <Button variant={theme === "" ? "primary" : "outline"} size="sm" onClick={() => { setTheme(""); setPage(1); }}>
          全部主题
        </Button>
        {groups?.map((g) => (
          <Button
            key={g.slug}
            variant={theme === g.slug ? "primary" : "outline"}
            size="sm"
            onClick={() => { setTheme(g.slug); setPage(1); }}
          >
            {g.name_zh}
          </Button>
        ))}
      </div>

      <input
        type="text"
        placeholder="搜索单词..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      />

      {isLoading ? (
        <Spinner />
      ) : (
        <>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {data?.items.map((w) => (
              <Card
                key={w.id}
                className={`cursor-pointer transition-all ${selected.includes(w.id) ? "ring-2 ring-primary-500" : ""} ${familiarityColor(w.familiarity)}`}
                onClick={() => toggleSelect(w.id)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-lg font-semibold">{w.lemma}</span>
                    {w.pos && <span className="ml-2 text-sm text-slate-500">{w.pos}</span>}
                  </div>
                  <Badge variant={w.level === "cet6" ? "purple" : "default"}>{w.level}</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-600">{w.definitions[0]}</p>
                {w.familiarity != null && w.familiarity > 0 && (
                  <p className="mt-2 text-xs text-slate-500">熟悉度: {w.familiarity}/5</p>
                )}
              </Card>
            ))}
          </div>

          <div className="flex justify-center gap-2">
            <Button variant="outline" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <span className="flex items-center px-4 text-sm text-slate-600">
              第 {page} 页 / 共 {Math.ceil((data?.total || 0) / 30)} 页
            </span>
            <Button
              variant="outline"
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
