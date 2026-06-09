"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Headphones, MessageCircle, Mic, BookOpen, PenLine, Play, Pause } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { Badge, Button, Card, Spinner, Tabs, Textarea } from "@/components/ui";
import type { ScenarioDetail } from "@/lib/api";

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
}: {
  word: string;
  usage: WordUsage | undefined;
}) {
  return (
    <div className="rounded-xl border border-brand-200 bg-brand-50/80 p-4">
      <p className="text-lg font-bold text-brand-900">{word}</p>
      {usage?.meaning_zh ? (
        <p className="mt-1 text-base text-amber-800">{usage.meaning_zh}</p>
      ) : (
        <p className="mt-1 text-sm text-amber-700">暂无中文释义</p>
      )}
      {usage?.sentence && (
        <p className="mt-3 text-sm text-slate-700">
          <span className="font-medium text-slate-500">例句：</span>
          {usage.sentence}
        </p>
      )}
    </div>
  );
}

export default function ScenarioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const [tab, setTab] = useState("read");
  const [playing, setPlaying] = useState(false);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [selectedWord, setSelectedWord] = useState<string | null>(null);
  const [recording, setRecording] = useState(false);
  const [speakResult, setSpeakResult] = useState<{ match_rate: number; feedback: string; transcript: string } | null>(null);
  const [writingContent, setWritingContent] = useState("");
  const [writingResult, setWritingResult] = useState<Awaited<ReturnType<typeof api.evaluateWriting>> | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const { data: scenario, isLoading } = useQuery({
    queryKey: ["scenario", id],
    queryFn: () => api.getScenario(Number(id)),
  });

  const startChat = useMutation({
    mutationFn: () =>
      api.createConversation({
        scenario_id: Number(id),
        level: scenario?.level ?? "cet4",
      }),
    onSuccess: (data) => router.push(`/chat/${data.id}`),
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
                router.push(`/login?next=/scenarios/${id}`);
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

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-4">
          {tab === "read" && (
            <Card>
              <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                <BookOpen className="h-4 w-4" /> 阅读模式 · 点击高亮词查看释义
              </div>
              <div className="leading-relaxed text-slate-800">
                {highlightPassage(scenario.content.passage, scenario.words, highlightOptions)}
              </div>
              {selectedWord && (
                <div className="mt-4">
                  <WordDefinitionPanel word={selectedWord} usage={selectedUsage} />
                </div>
              )}
              {scenario.dialogue.length > 0 && (
                <div className="mt-6 space-y-3 border-t pt-4">
                  <h3 className="font-medium">对话</h3>
                  {scenario.dialogue.map((d, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 p-3">
                      <span className="font-semibold text-brand-700">{d.speaker}:</span>{" "}
                      {highlightPassage(d.text, scenario.words, highlightOptions)}
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
              <Button className="mt-4" onClick={submitWriting}>提交批改</Button>
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

          {scenario.content.fun_fact && (
            <Card className="border-accent-400/30 bg-gradient-to-r from-teal-50 to-brand-50/50">
              <p className="text-sm font-bold text-accent-600">趣味知识</p>
              <p className="mt-1 text-slate-700">{scenario.content.fun_fact}</p>
            </Card>
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <h3 className="font-semibold">目标词汇</h3>
            <div className="mt-3 flex flex-wrap gap-2">
              {scenario.words.map((w) => (
                <button
                  key={w}
                  onClick={() => setSelectedWord(selectedWord === w ? null : w)}
                  className="rounded-full bg-brand-100 px-3 py-1 text-sm font-medium text-brand-800 transition-colors hover:bg-brand-200"
                >
                  {w}
                </button>
              ))}
            </div>
            {selectedWord && (
              <div className="mt-3">
                <WordDefinitionPanel word={selectedWord} usage={selectedUsage} />
              </div>
            )}
          </Card>
          <Card>
            <p className="text-sm text-slate-500">练习题</p>
            <p className="text-2xl font-bold">{scenario.exercise_count}</p>
            <Link href={`/scenarios/${id}/practice`}>
              <Button className="mt-3 w-full" variant="outline">去做练习</Button>
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
}
