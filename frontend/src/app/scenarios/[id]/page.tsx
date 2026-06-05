"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useRef, useState } from "react";
import { Headphones, Mic, BookOpen, PenLine, Play, Pause } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Button, Card, Spinner, Tabs } from "@/components/ui";

function highlightPassage(passage: string, words: string[]) {
  if (!words.length) return passage;
  const pattern = new RegExp(`\\b(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "gi");
  const parts = passage.split(pattern);
  return parts.map((part, i) =>
    words.some((w) => w.toLowerCase() === part.toLowerCase()) ? (
      <span key={i} className="highlight-word" title="目标词">{part}</span>
    ) : (
      part
    ),
  );
}

export default function ScenarioDetailPage() {
  const { id } = useParams<{ id: string }>();
  const deviceId = getDeviceId();
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
      device_id: deviceId,
    });
    setWritingResult(result);
  };

  if (isLoading) return <Spinner />;
  if (!scenario) return <Card>场景不存在</Card>;

  const shadowSentence = scenario.content.word_usage[0]?.sentence || scenario.content.passage.split(".")[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex gap-2">
            <Badge>{scenario.level.toUpperCase()}</Badge>
            <Badge variant="purple">{scenario.theme}</Badge>
          </div>
          <h1 className="mt-2 text-2xl font-bold">{scenario.title}</h1>
          <p className="mt-1 text-slate-600">{scenario.content.summary_zh}</p>
        </div>
        <Link href={`/scenarios/${id}/practice`}>
          <Button size="lg">开始练习</Button>
        </Link>
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
              <p className="leading-relaxed text-slate-800">
                {highlightPassage(scenario.content.passage, scenario.words)}
              </p>
              {scenario.dialogue.length > 0 && (
                <div className="mt-6 space-y-3 border-t pt-4">
                  <h3 className="font-medium">对话</h3>
                  {scenario.dialogue.map((d, i) => (
                    <div key={i} className="rounded-lg bg-slate-50 p-3">
                      <span className="font-medium text-primary-700">{d.speaker}:</span>{" "}
                      {highlightPassage(d.text, scenario.words)}
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
              <textarea
                value={writingContent}
                onChange={(e) => setWritingContent(e.target.value)}
                rows={6}
                className="w-full rounded-lg border border-slate-300 p-3 focus:border-primary-500 focus:outline-none"
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
            <Card className="border-amber-200 bg-amber-50">
              <p className="text-sm font-medium text-amber-800">趣味知识</p>
              <p className="mt-1 text-amber-900">{scenario.content.fun_fact}</p>
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
                  className="rounded-full bg-primary-50 px-3 py-1 text-sm text-primary-700 hover:bg-primary-100"
                >
                  {w}
                </button>
              ))}
            </div>
            {selectedWord && (
              <div className="mt-3 rounded-lg bg-slate-50 p-3 text-sm">
                {scenario.content.word_usage.find((u) => u.word.toLowerCase() === selectedWord.toLowerCase())?.sentence || "暂无例句"}
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
