"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Headphones, Search, Volume2, X } from "lucide-react";
import { api, PhoneticBrief, PhoneticDetail } from "@/lib/api";
import { cn } from "@/lib/utils";
import { useAudioPlayer } from "@/hooks/use-audio-player";
import { AudioPlayButton } from "@/components/audio-play-button";
import { MobileDetailSheet } from "@/components/reference/mobile-detail-sheet";
import { Alert, Badge, Button, Card, Input, Spinner, StatCard } from "@/components/ui";

function phoneticAudioUrl(phoneticId: number, previewWord?: string | null) {
  if (previewWord) {
    return api.getPhoneticAudioUrl(phoneticId, { word: previewWord });
  }
  return api.getPhoneticAudioUrl(phoneticId, { kind: "symbol" });
}

function PhoneticCard({
  item,
  active,
  onClick,
  player,
}: {
  item: PhoneticBrief;
  active: boolean;
  onClick: () => void;
  player: ReturnType<typeof useAudioPlayer>;
}) {
  const symbolAudioKey = `phonetic-word-${item.id}-${item.preview_word ?? "symbol"}`;

  return (
    <div
      className={cn(
        "relative rounded-xl border p-4 transition-all",
        active
          ? "border-brand-300 bg-brand-50/80 shadow-sm ring-2 ring-brand-200"
          : "border-surface-border bg-white/80 hover:border-brand-200 hover:bg-brand-50/40",
      )}
    >
      <button type="button" onClick={onClick} className="w-full text-left">
        <div className="flex items-start justify-between gap-2 pr-10">
          <span className="font-display text-2xl font-bold text-brand-700">{item.symbol}</span>
          {item.subcategory && <Badge variant="outline">{item.subcategory}</Badge>}
        </div>
        <p className="mt-2 font-medium text-slate-800">{item.name_zh}</p>
        <p className="mt-0.5 text-xs text-slate-500">{item.name_en}</p>
      </button>

      <div className="absolute right-3 top-3">
        <AudioPlayButton
          audioKey={symbolAudioKey}
          url={phoneticAudioUrl(item.id, item.preview_word)}
          player={player}
          label={item.preview_word ? `播放例词 ${item.preview_word}` : `播放 /${item.symbol}/ 读音`}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  );
}

function PhoneticDetailPanel({
  detail,
  onClose,
  player,
}: {
  detail: PhoneticDetail;
  onClose: () => void;
  player: ReturnType<typeof useAudioPlayer>;
}) {
  const primaryWord = detail.examples[0]?.word ?? detail.sound_cue ?? null;
  const symbolAudioKey = `phonetic-word-${detail.id}-${primaryWord ?? "symbol"}`;
  const allAudioKey = `phonetic-all-${detail.id}`;

  return (
    <Card glass={false} className="space-y-4 border-0 bg-transparent p-0 shadow-none lg:glass-card lg:sticky-below-header lg:border lg:bg-white/80 lg:p-5 lg:shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-brand-600">音标详情</p>
          <div className="mt-1 flex items-center gap-3">
            <p className="font-display text-4xl font-bold text-brand-700">{detail.symbol}</p>
            <AudioPlayButton
              audioKey={symbolAudioKey}
              url={phoneticAudioUrl(detail.id, primaryWord)}
              player={player}
              size="md"
              label={primaryWord ? `播放例词 ${primaryWord}` : `播放 /${detail.symbol}/ 读音`}
            />
          </div>
          <p className="mt-1 text-lg font-medium text-slate-800">{detail.name_zh}</p>
          <p className="text-sm text-slate-500">{detail.name_en}</p>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {primaryWord && (
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => void player.toggle(phoneticAudioUrl(detail.id, primaryWord), symbolAudioKey)}
        >
          <Volume2 className="mr-2 h-4 w-4" />
          {player.isPlaying(symbolAudioKey) ? "暂停" : `播放例词 ${primaryWord}`}
        </Button>
      )}

      {detail.examples.length > 0 && (
        <Button
          variant="ghost"
          size="sm"
          className="w-full border border-surface-border"
          onClick={() => void player.toggle(api.getPhoneticAudioUrl(detail.id, { kind: "examples" }), allAudioKey)}
        >
          <Headphones className="mr-2 h-4 w-4" />
          {player.isPlaying(allAudioKey) ? "暂停例词朗读" : "播放全部例词"}
        </Button>
      )}

      {detail.description && (
        <p className="rounded-xl bg-slate-50 px-4 py-3 text-sm leading-relaxed text-slate-700">
          {detail.description}
        </p>
      )}

      {detail.examples.length > 0 && (
        <div>
          <h3 className="mb-2 text-sm font-semibold text-slate-700">例词</h3>
          <div className="space-y-2">
            {detail.examples.map((ex) => {
              const wordKey = `phonetic-word-${detail.id}-${ex.word}`;
              return (
                <div
                  key={`${ex.word}-${ex.ipa}`}
                  className="flex items-center justify-between gap-3 rounded-xl border border-surface-border bg-white px-4 py-3"
                >
                  <div className="min-w-0">
                    <span className="font-semibold text-slate-900">{ex.word}</span>
                    <span className="ml-2 font-mono text-sm text-brand-600">{ex.ipa}</span>
                    <p className="mt-0.5 text-sm text-slate-500">{ex.meaning_zh}</p>
                  </div>
                  <AudioPlayButton
                    audioKey={wordKey}
                    url={api.getPhoneticAudioUrl(detail.id, { word: ex.word })}
                    player={player}
                    label={`播放 ${ex.word}`}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
}

export default function PhoneticsPage() {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const player = useAudioPlayer();

  const { data, isLoading } = useQuery({
    queryKey: ["phonetics", category, search],
    queryFn: () => api.getPhonetics({ ...(category && { category }), ...(search && { search }) }),
  });

  const { data: detail, isLoading: detailLoading } = useQuery({
    queryKey: ["phonetic", selectedId],
    queryFn: () => api.getPhonetic(selectedId!),
    enabled: selectedId !== null,
  });

  const categories = data?.groups.map((g) => ({ id: g.category, label: g.category_zh, count: g.count })) ?? [];
  const vowelCount =
    (data?.groups.find((g) => g.category === "short_vowel")?.count ?? 0) +
    (data?.groups.find((g) => g.category === "long_vowel")?.count ?? 0) +
    (data?.groups.find((g) => g.category === "diphthong")?.count ?? 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="音标总数" value={data?.total ?? "—"} icon={Volume2} tone="brand" />
        <StatCard label="元音" value={vowelCount} icon={Volume2} tone="violet" />
        <StatCard label="辅音" value={data?.groups.find((g) => g.category === "consonant")?.count ?? 0} icon={Volume2} tone="emerald" />
      </div>

      {player.error && <Alert variant="warning">{player.error}</Alert>}

      <Card className="space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="搜索音标、中文或英文名称..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => setCategory("")}
            className={cn(
              "rounded-full px-3 py-1.5 text-xs font-semibold transition-all",
              !category ? "bg-hero-gradient text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200",
            )}
          >
            全部
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setCategory(c.id)}
              className={cn(
                "rounded-full px-3 py-1.5 text-xs font-semibold transition-all",
                category === c.id ? "bg-hero-gradient text-white shadow-sm" : "bg-slate-100 text-slate-600 hover:bg-slate-200",
              )}
            >
              {c.label} ({c.count})
            </button>
          ))}
        </div>
      </Card>

      {isLoading ? (
        <Spinner label="加载音标..." />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="space-y-8">
            {data?.groups.map((group) => (
              <section key={group.category}>
                <div className="mb-4 flex items-center gap-2">
                  <h2 className="text-lg font-bold text-slate-900">{group.category_zh}</h2>
                  <Badge variant="brand">{group.count}</Badge>
                </div>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {group.items.map((item) => (
                    <PhoneticCard
                      key={item.id}
                      item={item}
                      active={selectedId === item.id}
                      onClick={() => setSelectedId(item.id)}
                      player={player}
                    />
                  ))}
                </div>
              </section>
            ))}
          </div>

          <aside className="hidden lg:block">
            {selectedId === null ? (
              <Card className="sticky-below-header text-center text-sm text-slate-500">
                <Volume2 className="mx-auto mb-3 h-8 w-8 text-brand-300" />
                点击左侧音标查看详情，或点 🔊 试听音标本身发音
              </Card>
            ) : detailLoading ? (
              <Spinner label="加载详情..." />
            ) : detail ? (
              <PhoneticDetailPanel detail={detail} onClose={() => setSelectedId(null)} player={player} />
            ) : null}
          </aside>
        </div>
      )}

      <MobileDetailSheet open={selectedId !== null} onClose={() => setSelectedId(null)}>
        {detailLoading ? (
          <Spinner label="加载详情..." />
        ) : detail ? (
          <PhoneticDetailPanel detail={detail} onClose={() => setSelectedId(null)} player={player} />
        ) : null}
      </MobileDetailSheet>
    </div>
  );
}
