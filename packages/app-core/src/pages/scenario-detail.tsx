"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "@sceneenglish/app-core/components/platform-link";
import { useParams, useNavigate } from "@sceneenglish/app-core/platform/context";
import { useRef, useState } from "react";
import { Headphones, MessageCircle, Mic, BookOpen, PenLine, Play, Pause, Languages, Sparkles } from "lucide-react";
import { api } from "@sceneenglish/api-client";
import { useAuth } from "@sceneenglish/app-core/contexts/auth-context";
import { Badge, Button, Card, Spinner, Tabs, Textarea } from "@sceneenglish/app-core/components/ui";
import { cn } from "@sceneenglish/app-core/lib/utils";
import type { ScenarioDetail } from "@sceneenglish/api-client";

type WordUsage = ScenarioDetail["content"]["word_usage"][number];

function findWordUsage(wordUsage: WordUsage[], word: string): WordUsage | undefined {
  return wordUsage.find((u) => u.word.toLowerCase() === word.toLowerCase());
}

function highlightPassage(
  passage: string,
  words: string[],
  options?: {
    selectedWord?: string | null;
    onWordClick?: (word: string) => void;
  },
) {
  if (!words.length) return passage;
  const pattern = new RegExp(`\\b(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "gi");
  const parts = passage.split(pattern);
  return parts.map((part, i) => {
    const matched = words.find((w) => w.toLowerCase() === part.toLowerCase());
    if (!matched) return part;
    const isSelected = options?.selectedWord?.toLowerCase() === matched.toLowerCase();
    return (
      <button
        key={i}
        type="button"
        className={`highlight-word ${isSelected ? "highlight-word-active" : ""}`}
        onClick={() => options?.onWordClick?.(matched)}
        aria-pressed={isSelected}
        aria-label={`查看 ${matched} 的释义`}
      >
        {part}
      </button>
    );
  });
}

function WordDefinitionPanel({
  word,
  usage,
  compact = false,
}: {
  word: string;
  usage: WordUsage | undefined;
  compact?: boolean;
}) {
  const meaning = usage?.meaning_zh?.trim();
  const showMeaning = Boolean(meaning && meaning.toLowerCase() !== word.toLowerCase());

  return (
    <div className={cn(
      "rounded-xl border border-brand-200 bg-brand-50/80",
      compact ? "p-3" : "p-4",
    )}>
      <p className={cn("font-bold text-brand-900", compact ? "text-base" : "text-lg")}>{word}</p>
      {showMeaning ? (
        <p className={cn("mt-1 text-amber-800", compact ? "text-sm" : "text-base")}>{meaning}</p>
      ) : (
        <p className="mt-1 text-sm text-amber-700">暂无中文释义</p>
      )}
      {usage?.sentence && !compact && (
        <p className="mt-3 text-sm leading-relaxed text-slate-700">
          <span className="font-medium text-slate-500">例句：</span>
          {usage.sentence}
        </p>
      )}
    </div>
  );
}

function VocabularyChips({
  words,
  selectedWord,
  onSelect,
  size = "default",
}: {
  words: string[];
  selectedWord: string | null;
  onSelect: (word: string) => void;
  size?: "default" | "sm";
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {words.map((w) => (
        <button
          key={w}
          type="button"
          onClick={() => onSelect(w)}
          className={cn(
            "shrink-0 rounded-full font-medium transition-colors",
            size === "sm" ? "px-2.5 py-0.5 text-xs" : "px-3 py-1 text-sm",
            selectedWord === w
              ? "bg-brand-600 text-white"
              : "bg-brand-100 text-brand-800 hover:bg-brand-200",
          )}
        >
          {w}
        </button>
      ))}
    </div>
  );
}

const TAB_SIDEBAR_HINTS: Record<string, string> = {
  read: "点击正文高亮词或上方标签查看释义",
  listen: "建议先完整听一遍，再切回阅读对照原文",
  speak: "跟读句子中包含场景核心词汇",
  write: "写作时尽量自然运用标亮的目标词",
};

export default function ScenarioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [tab, setTab] = useState("read");
  const [playing, setPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const [recording, setRecording] = useState(false);
  const [speakResult, setSpeakResult] = useState<{ match_rate: number; feedback: string; transcript: string } | null>(null);
  const [writingContent, setWritingContent] = useState("");
  const [writingResult, setWritingResult] = useState<Awaited<ReturnType<typeof api.evaluateWriting>> | null>(null);
  const [writingSample, setWritingSample] = useState<Awaited<ReturnType<typeof api.generateWritingSample>> | null>(null);
  const [showWritingSample, setShowWritingSample] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const { data: scenario, isLoading } = useQuery({
    queryKey: ["scenario", id],
    queryFn: () => api.getScenario(Number(id)),
  });

  const { data: translation, isLoading: translationLoading, isFetching: translationFetching } = useQuery({
    queryKey: ["scenario-translation", id],
    queryFn: () => api.getScenarioTranslation(Number(id)),
    enabled: showTranslation && Boolean(id),
    staleTime: Infinity,
  });

  const startChat = useMutation({
    mutationFn: () =>
      api.createConversation({
        scenario_id: Number(id),
        level: scenario?.level ?? "cet4",
      }),
    onSuccess: (data) => navigate(`/chat/${data.id}`),
  });

  const toggleAudio = () => {
    if (!audioRef.current) return;
    if (playing) {
      audioRef.current.pause();
    } else {
      audioRef.current.playbackRate = playbackRate;
      audioRef.current.play();
    }
    setPlaying(!playing);
  };

  const startRecording = async (sentence: string) => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    chunksRef.current = [];
    recorder.ondataavailable = (e) => chunksRef.current.push(e.data);
    recorder.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: "audio/webm" });
      stream.getTracks().forEach((t) => t.stop());
      const result = await api.evaluateSpeaking(sentence, blob);
      setSpeakResult(result);
    };
    recorder.start();
    mediaRecorderRef.current = recorder;
    setRecording(true);
    (window as unknown as { _shadowSentence: string })._shadowSentence = sentence;
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setRecording(false);
  };

  const submitWriting = async () => {
    if (!scenario) return;
    const result = await api.evaluateWriting({
      prompt: `Write a short paragraph using these words: ${scenario.words.join(", ")}`,
      content: writingContent,
      target_words: scenario.words.slice(0, 5),
    });
    setWritingResult(result);
  };

  const generateWritingSample = useMutation({
    mutationFn: ({ regenerate }: { regenerate: boolean }) => {
      if (!scenario) throw new Error("Scenario not loaded");
      const targetWords = scenario.words.slice(0, 5);
      return api.generateWritingSample({
        prompt: `Write a short paragraph of about 80 words using these words: ${targetWords.join(", ")}`,
        target_words: targetWords,
        level: scenario.level,
        theme: scenario.theme,
        regenerate,
      });
    },
    onSuccess: (data) => {
      setWritingSample(data);
      setShowWritingSample(true);
    },
  });

  const handleGenerateWritingSample = () => {
    generateWritingSample.mutate({ regenerate: Boolean(writingSample) });
  };

  if (isLoading) return <Spinner label="加载场景..." />;
  if (!scenario) return <Card>场景不存在</Card>;

  const shadowSentence = scenario.content.word_usage[0]?.sentence || scenario.content.passage.split(".")[0];
  const selectedUsage = selectedWord
    ? findWordUsage(scenario.content.word_usage, selectedWord)
    : undefined;
  const highlightOptions = {
    selectedWord,
    onWordClick: (word: string) => setSelectedWord((prev) => (prev === word ? null : word)),
  };
  const passageZh = translation?.passage_zh ?? scenario?.content.passage_zh;
  const dialogueZh = translation?.dialogue_zh ?? [];
  const translationPending = showTranslation && (translationLoading || translationFetching) && !passageZh;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap gap-2">
            <Badge variant="brand">{scenario.level.toUpperCase()}</Badge>
            <Badge variant="purple">{scenario.theme}</Badge>
          </div>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">{scenario.title}</h1>
          <p className="mt-2 text-slate-600">{scenario.content.summary_zh}</p>
        </div>
        <div className="flex shrink-0 flex-row flex-wrap items-center gap-2">
          <Button
            size="lg"
            variant="outline"
            disabled={startChat.isPending}
            onClick={() => {
              if (!isAuthenticated) {
                navigate(`/login?next=/scenarios/${id}`);
                return;
              }
              startChat.mutate();
            }}
          >
            <MessageCircle className="mr-2 h-4 w-4 shrink-0" />
            1v1 对话
          </Button>
          <Link href={`/scenarios/${id}/practice`} className="inline-flex shrink-0">
            <Button size="lg">开始练习</Button>
          </Link>
        </div>
      </div>

      <Tabs
        tabs={[
          { id: "read", label: "阅读" },
          { id: "listen", label: "听力" },
          { id: "speak", label: "口语" },
          { id: "write", label: "写作" },
        ]}
        active={tab}
        onChange={setTab}
      />

      <div className="rounded-2xl border border-surface-border bg-white/70 px-4 py-3 shadow-sm backdrop-blur-sm lg:hidden">
        <div className="flex items-center justify-between gap-3">
          <p className="shrink-0 text-xs font-semibold text-slate-500">目标词汇</p>
          {scenario.exercise_count > 0 && (
            <Link
              href={`/scenarios/${id}/practice`}
              className="shrink-0 text-xs font-medium text-brand-700 hover:text-brand-800"
            >
              {scenario.exercise_count} 题 · 去练习
            </Link>
          )}
        </div>
        <div className="mt-2">
          <VocabularyChips
            words={scenario.words}
            selectedWord={selectedWord}
            onSelect={(word) => setSelectedWord((prev) => (prev === word ? null : word))}
            size="sm"
          />
        </div>
        {selectedWord ? (
          <div className="mt-3">
            <WordDefinitionPanel word={selectedWord} usage={selectedUsage} compact />
          </div>
        ) : (
          <p className="mt-2 text-xs text-slate-500">{TAB_SIDEBAR_HINTS[tab]}</p>
        )}
        {scenario.content.fun_fact && (
          <div className="mt-3 border-t border-surface-border/60 pt-3">
            <p className="text-xs font-semibold text-accent-600">趣味知识</p>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{scenario.content.fun_fact}</p>
          </div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {tab === "read" && (
            <Card>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm text-slate-500">
                  <BookOpen className="h-4 w-4" /> 阅读模式 · 点击高亮词查看释义
                </div>
                <Button
                  type="button"
                  variant={showTranslation ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setShowTranslation((value) => !value)}
                >
                  <Languages className="mr-1.5 h-4 w-4" />
                  {showTranslation ? "隐藏译文" : "显示译文"}
                </Button>
              </div>
              <div className="reading-text text-slate-800">
                {highlightPassage(scenario.content.passage, scenario.words, highlightOptions)}
              </div>
              {showTranslation && (
                <div className="mt-4 rounded-xl border border-surface-border bg-slate-50/90 p-4 animate-fade-in">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">中文译文</p>
                  {translationPending ? (
                    <Spinner label="正在生成译文..." />
                  ) : passageZh ? (
                    <p className="reading-text text-slate-700">{passageZh}</p>
                  ) : (
                    <p className="text-sm text-slate-500">暂无译文</p>
                  )}
                </div>
              )}
              {scenario.dialogue.length > 0 && (
                <div className="mt-6 space-y-3 border-t pt-4">
                  <h3 className="font-medium">对话</h3>
                  {scenario.dialogue.map((d, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 p-3 reading-text">
                      <span className="font-semibold text-brand-700">{d.speaker}:</span>{" "}
                      {highlightPassage(d.text, scenario.words, highlightOptions)}
                      {showTranslation && dialogueZh[i]?.text && (
                        <p className="mt-2 border-t border-surface-border/60 pt-2 text-sm text-slate-600">
                          {dialogueZh[i].text}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </Card>
          )}

          {tab === "listen" && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                <Headphones className="h-4 w-4" /> 听力模式 · 先听再理解
              </div>
              <audio
                ref={audioRef}
                src={api.getScenarioAudioUrl(Number(id))}
                onEnded={() => setPlaying(false)}
              />
              <div className="flex items-center gap-4">
                <Button onClick={toggleAudio}>
                  {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                  <span className="ml-2">{playing ? "暂停" : "播放"}</span>
                </Button>
                {[0.75, 1, 1.25].map((rate) => (
                  <Button
                    key={rate}
                    variant={playbackRate === rate ? "primary" : "outline"}
                    size="sm"
                    onClick={() => {
                      setPlaybackRate(rate);
                      if (audioRef.current) audioRef.current.playbackRate = rate;
                    }}
                  >
                    {rate}x
                  </Button>
                ))}
              </div>
              <p className="mt-6 text-sm text-slate-500">听完音频后，进入练习页完成听力理解题</p>
            </Card>
          )}

          {tab === "speak" && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                <Mic className="h-4 w-4" /> 跟读模式
              </div>
              <p className="text-lg leading-relaxed">{shadowSentence}</p>
              <div className="mt-4">
                {!recording ? (
                  <Button onClick={() => startRecording(shadowSentence)}>
                    <Mic className="mr-2 h-4 w-4" /> 开始录音
                  </Button>
                ) : (
                  <Button variant="secondary" onClick={stopRecording}>
                    停止并评测
                  </Button>
                )}
              </div>
              {speakResult && (
                <div className="mt-4 rounded-lg bg-slate-50 p-4">
                  <p className="font-medium">匹配率: {speakResult.match_rate}%</p>
                  <p className="mt-1 text-sm text-slate-600">识别: {speakResult.transcript}</p>
                  <p className="mt-2 text-sm">{speakResult.feedback}</p>
                </div>
              )}
            </Card>
          )}

          {tab === "write" && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                <PenLine className="h-4 w-4" /> 写作练习
              </div>
              <p className="text-sm text-slate-600 mb-4">
                用以下词汇写一段 80 词左右的短文：{scenario.words.slice(0, 5).join(", ")}
              </p>
              <Textarea
                value={writingContent}
                onChange={(e) => setWritingContent(e.target.value)}
                rows={6}
                placeholder="Start writing here..."
              />
              <div className="mt-4 flex flex-wrap gap-2">
                <Button onClick={submitWriting} disabled={!writingContent.trim()}>
                  提交批改
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleGenerateWritingSample}
                  disabled={generateWritingSample.isPending}
                >
                  <Sparkles className="mr-1.5 h-4 w-4" />
                  {generateWritingSample.isPending
                    ? "生成中..."
                    : writingSample
                      ? "重新生成"
                      : "AI 参考范文"}
                </Button>
                {writingSample && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowWritingSample((value) => !value)}
                  >
                    {showWritingSample ? "隐藏参考" : "显示参考"}
                  </Button>
                )}
              </div>
              {(showWritingSample || generateWritingSample.isPending) && (
                <div className="mt-4 space-y-3 rounded-xl border border-brand-200/60 bg-brand-50/40 p-4 animate-fade-in">
                  <p className="text-xs font-semibold uppercase tracking-wide text-brand-700">AI 参考范文</p>
                  {generateWritingSample.isPending ? (
                    <Spinner label="正在生成新的参考范文..." />
                  ) : writingSample ? (
                    <>
                      <p className="reading-text text-slate-800">{writingSample.sample_en}</p>
                      {writingSample.sample_zh && (
                        <p className="border-t border-brand-200/50 pt-3 text-sm text-slate-600">{writingSample.sample_zh}</p>
                      )}
                    </>
                  ) : null}
                </div>
              )}
              {writingResult && (
                <div className="mt-4 rounded-lg bg-slate-50 p-4 space-y-2 text-sm">
                  <p className="font-medium">得分: {writingResult.score}</p>
                  <p>{writingResult.grammar_feedback}</p>
                  <p>{writingResult.vocabulary_feedback}</p>
                  {writingResult.suggestions.map((s, i) => (
                    <p key={i} className="text-slate-600">· {s}</p>
                  ))}
                </div>
              )}
            </Card>
          )}
        </div>

        <aside className="hidden space-y-4 lg:block lg:sticky lg:top-6 lg:self-start">
          <Card>
            <h3 className="font-semibold">目标词汇</h3>
            <div className="mt-3">
              <VocabularyChips
                words={scenario.words}
                selectedWord={selectedWord}
                onSelect={(word) => setSelectedWord((prev) => (prev === word ? null : word))}
              />
            </div>
            <div className="mt-3">
              {selectedWord ? (
                <WordDefinitionPanel word={selectedWord} usage={selectedUsage} />
              ) : (
                <p className="text-sm text-slate-500">{TAB_SIDEBAR_HINTS[tab]}</p>
              )}
            </div>

            {(scenario.content.fun_fact || scenario.exercise_count > 0) && (
              <div className="mt-4 space-y-3 border-t border-surface-border pt-4">
                {scenario.content.fun_fact && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-accent-600">趣味知识</p>
                    <p className="mt-1 text-sm leading-relaxed text-slate-700">{scenario.content.fun_fact}</p>
                  </div>
                )}
                {scenario.exercise_count > 0 && (
                  <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2.5">
                    <div>
                      <p className="text-xs text-slate-500">配套练习</p>
                      <p className="text-lg font-bold text-slate-900">{scenario.exercise_count} 题</p>
                    </div>
                    <Link href={`/scenarios/${id}/practice`}>
                      <Button size="sm" variant="outline">去做练习</Button>
                    </Link>
                  </div>
                )}
              </div>
            )}
          </Card>
        </aside>
      </div>
    </div>
  );
}
