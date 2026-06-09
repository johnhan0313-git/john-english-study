"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import {
  loadWordsViewMode,
  pageSizeForView,
  saveWordsViewMode,
  type WordsViewMode,
} from "@/lib/words-display";
import { Button, Card, Input, PageHeader, Spinner } from "@/components/ui";
import { WordsViewSwitcher } from "@/components/words/view-switcher";
import { WordsGridView } from "@/components/words/views/grid-view";
import { WordsListView } from "@/components/words/views/list-view";
import { WordsTableView } from "@/components/words/views/table-view";
import { WordsFlashcardView } from "@/components/words/views/flashcard-view";
import { WordsIndexView } from "@/components/words/views/index-view";

const LEVEL_FILTERS: { value: string; label: string }[] = [
  { value: "", label: "全部级别" },
  { value: "cet4", label: "CET-4" },
  { value: "cet6", label: "CET-6" },
  { value: "pets1", label: "PETS-1" },
  { value: "pets2", label: "PETS-2" },
  { value: "pets3", label: "PETS-3" },
  { value: "pets4", label: "PETS-4" },
  { value: "pets5", label: "PETS-5" },
];

export default function WordsPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [level, setLevel] = useState<string>("");
  const [theme, setTheme] = useState<string>("");
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<WordsViewMode>("grid");

  useEffect(() => {
    setViewMode(loadWordsViewMode());
  }, []);

  const pageSize = pageSizeForView(viewMode);

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["words", page, pageSize, level, theme, search, user?.id ?? "guest"],
    queryFn: () =>
      api.getWords({
        page,
        page_size: pageSize,
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

  const handleViewChange = (mode: WordsViewMode) => {
    setViewMode(mode);
    saveWordsViewMode(mode);
    setPage(1);
  };

  const totalPages = Math.ceil((data?.total || 0) / pageSize) || 1;
  const items = data?.items ?? [];

  const renderView = () => {
    const props = { words: items, selected, onToggle: toggleSelect };
    switch (viewMode) {
      case "list":
        return <WordsListView {...props} />;
      case "table":
        return <WordsTableView {...props} />;
      case "flashcard":
        return <WordsFlashcardView {...props} />;
      case "index":
        return <WordsIndexView {...props} />;
      default:
        return <WordsGridView {...props} />;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        badge="词汇库"
        title="CET / PETS 词库"
        description={`共 ${data?.total ?? "..."} 词 · CET-4/6 + 全国公共英语等级考试 · 点击选词可批量生成场景`}
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
        <WordsViewSwitcher value={viewMode} onChange={handleViewChange} />
        <div className="flex flex-wrap gap-2">
          {LEVEL_FILTERS.map(({ value, label }) => (
            <button
              key={value || "all"}
              type="button"
              className={level === value ? "chip-active" : "chip-inactive"}
              onClick={() => { setLevel(value); setPage(1); }}
            >
              {label}
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
          {renderView()}

          <div className="flex items-center justify-center gap-3 pt-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <span className="rounded-full bg-white/80 px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm">
              {page} / {totalPages}
              {viewMode === "index" && (
                <span className="ml-1 text-xs text-slate-400">· 每页 {pageSize} 词</span>
              )}
            </span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              下一页
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
