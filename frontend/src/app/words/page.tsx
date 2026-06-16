"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import Link from "next/link";
import { Search, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { useAudioPlayer } from "@/hooks/use-audio-player";
import {
  pageSizeForView,
  type WordsViewMode,
} from "@/lib/words-display";
import { Button, Card, Input, PageHeader, Spinner } from "@/components/ui";
import { WordsViewSwitcher } from "@/components/words/view-switcher";
import { WordsAlphabetLayout } from "@/components/words/words-alphabet-layout";
import { WordsGridView } from "@/components/words/views/grid-view";
import { WordsListView } from "@/components/words/views/list-view";

function FilterRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:gap-3">
      <span className="shrink-0 pt-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400 sm:w-10">
        {label}
      </span>
      <div className="flex min-w-0 flex-1 flex-wrap gap-2">{children}</div>
    </div>
  );
}

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
  const [letter, setLetter] = useState("");
  const [selected, setSelected] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<WordsViewMode>("grid");
  const player = useAudioPlayer();

  const pageSize = pageSizeForView(viewMode);

  const filterParams = {
    ...(level && { level }),
    ...(theme && { theme }),
    ...(search && { search }),
  };

  const { data: groups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const { data: letterIndex } = useQuery({
    queryKey: ["word-letters", level, theme, search],
    queryFn: () => api.getWordLetters(filterParams),
  });

  const { data, isLoading } = useQuery({
    queryKey: ["words", page, pageSize, level, theme, search, letter, user?.id ?? "guest"],
    queryFn: () =>
      api.getWords({
        page,
        page_size: pageSize,
        ...filterParams,
        ...(letter && { letter }),
      }),
  });

  const resetPage = () => {
    setPage(1);
  };

  const toggleSelect = (id: number) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 15 ? [...prev, id] : prev,
    );
  };

  const handleViewChange = (mode: WordsViewMode) => {
    setViewMode(mode);
    setPage(1);
  };

  const handleLetterSelect = (value: string) => {
    setLetter((prev) => (prev === value ? "" : value));
    setPage(1);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const totalPages = Math.ceil((data?.total || 0) / pageSize) || 1;
  const items = data?.items ?? [];
  const availableLetters = letterIndex?.letters ?? [];

  const renderView = (groups: Parameters<typeof WordsGridView>[0]["groups"]) => {
    const props = { groups, selected, onToggle: toggleSelect, player };
    return viewMode === "list" ? <WordsListView {...props} /> : <WordsGridView {...props} />;
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

      <Card className="space-y-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative min-w-0 flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <Input
              placeholder="搜索单词..."
              value={search}
              onChange={(e) => { setSearch(e.target.value); resetPage(); }}
              className="pl-10"
            />
          </div>
          <WordsViewSwitcher value={viewMode} onChange={handleViewChange} />
        </div>

        <div className="space-y-3 border-t border-surface-border/60 pt-4">
          <FilterRow label="级别">
            {LEVEL_FILTERS.map(({ value, label }) => (
              <button
                key={value || "all"}
                type="button"
                className={level === value ? "chip-active" : "chip-inactive"}
                onClick={() => { setLevel(value); resetPage(); }}
              >
                {label}
              </button>
            ))}
          </FilterRow>
          <FilterRow label="主题">
            <button
              type="button"
              className={theme === "" ? "chip-active" : "chip-inactive"}
              onClick={() => { setTheme(""); resetPage(); }}
            >
              全部主题
            </button>
            {groups?.map((g) => (
              <button
                key={g.slug}
                type="button"
                className={theme === g.slug ? "chip-active" : "chip-inactive"}
                onClick={() => { setTheme(g.slug); resetPage(); }}
              >
                {g.name_zh}
              </button>
            ))}
          </FilterRow>
        </div>
      </Card>

      {isLoading ? (
        <Spinner label="加载词库..." />
      ) : (
        <>
          <WordsAlphabetLayout
            words={items}
            total={data?.total ?? 0}
            availableLetters={availableLetters}
            selectedLetter={letter}
            onLetterSelect={handleLetterSelect}
          >
            {renderView}
          </WordsAlphabetLayout>

          <div className="flex items-center justify-center gap-3 pt-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              上一页
            </Button>
            <span className="rounded-full bg-white/80 px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm">
              {page} / {totalPages}
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
