"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import { api, Exercise } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Button, Card, ProgressBar, Spinner } from "@/components/ui";

function ExerciseItem({
  exercise,
  answer,
  onChange,
  result,
}: {
  exercise: Exercise;
  answer: string;
  onChange: (val: string) => void;
  result?: { correct: boolean; correct_answer: string | string[]; explanation?: string };
}) {
  if (exercise.type === "single_choice") {
    return (
      <div className="space-y-3">
        <p className="font-medium">{exercise.payload.question}</p>
        <div className="space-y-2">
          {exercise.payload.options?.map((opt) => (
            <label
              key={opt.label}
              className={`flex cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${
                answer === opt.label ? "border-primary-500 bg-primary-50" : "border-slate-200 hover:bg-slate-50"
              } ${result ? (result.correct_answer === opt.label ? "border-green-500 bg-green-50" : answer === opt.label && !result.correct ? "border-red-500 bg-red-50" : "") : ""}`}
            >
              <input
                type="radio"
                name={`ex-${exercise.id}`}
                value={opt.label}
                checked={answer === opt.label}
                onChange={() => onChange(opt.label)}
                disabled={!!result}
                className="sr-only"
              />
              <Badge>{opt.label}</Badge>
              <span>{opt.text}</span>
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (exercise.type === "fill_blank") {
    return (
      <div className="space-y-3">
        <p className="font-medium">{exercise.payload.question || "填空题"}</p>
        <p className="leading-relaxed text-slate-700">{exercise.payload.passage_with_blanks}</p>
        <input
          type="text"
          value={answer}
          onChange={(e) => onChange(e.target.value)}
          disabled={!!result}
          placeholder="填入答案..."
          className="w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-primary-500 focus:outline-none"
        />
      </div>
    );
  }

  return null;
}

export default function PracticePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const deviceId = getDeviceId();
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [results, setResults] = useState<Record<number, { correct: boolean; correct_answer: string | string[]; explanation?: string }>>({});
  const [finished, setFinished] = useState(false);
  const [batchScore, setBatchScore] = useState<{ score: number; correct: number; total: number } | null>(null);

  const { data: exercises, isLoading } = useQuery({
    queryKey: ["exercises", id],
    queryFn: () => api.getExercises(Number(id)),
  });

  const submitOne = useMutation({
    mutationFn: ({ exerciseId, answer }: { exerciseId: number; answer: string }) =>
      api.submitExercise(exerciseId, answer, deviceId),
    onSuccess: (data, vars) => {
      setResults((prev) => ({ ...prev, [vars.exerciseId]: data }));
    },
  });

  const handleNext = async () => {
    if (!exercises) return;
    const ex = exercises[currentIdx];
    const answer = answers[ex.id] || "";
    if (!answer) return;

    const result = await submitOne.mutateAsync({ exerciseId: ex.id, answer });
    const updatedResults = { ...results, [ex.id]: result };

    if (currentIdx < exercises.length - 1) {
      setCurrentIdx((i) => i + 1);
    } else {
      const correct = Object.values(updatedResults).filter((r) => r.correct).length;
      setBatchScore({ score: Math.round((correct / exercises.length) * 100), correct, total: exercises.length });
      setFinished(true);
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/scenarios/${id}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ device_id: deviceId, total: exercises.length, correct }),
      });
    }
  };

  if (isLoading) return <Spinner />;
  if (!exercises?.length) return <Card>暂无练习题</Card>;

  if (finished && batchScore) {
    return (
      <Card className="mx-auto max-w-lg text-center">
        <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
        <h2 className="mt-4 text-2xl font-bold">练习完成!</h2>
        <p className="mt-2 text-4xl font-bold text-primary-600">{batchScore.score} 分</p>
        <p className="text-slate-600">
          正确 {batchScore.correct} / {batchScore.total} 题
        </p>
        <div className="mt-6 flex justify-center gap-3">
          <Link href={`/scenarios/${id}`}>
            <Button variant="outline">返回场景</Button>
          </Link>
          <Link href="/">
            <Button>回首页</Button>
          </Link>
        </div>
      </Card>
    );
  }

  const current = exercises[currentIdx];
  const currentResult = results[current.id];
  const progress = ((currentIdx + (currentResult ? 1 : 0)) / exercises.length) * 100;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>第 {currentIdx + 1} / {exercises.length} 题</span>
          <Badge>{current.type === "single_choice" ? "单选题" : "填空题"}</Badge>
        </div>
        <ProgressBar value={progress} className="mt-2" />
      </div>

      <Card>
        <ExerciseItem
          exercise={current}
          answer={answers[current.id] || ""}
          onChange={(val) => setAnswers((prev) => ({ ...prev, [current.id]: val }))}
          result={currentResult}
        />

        {currentResult && (
          <div className={`mt-4 flex items-start gap-2 rounded-lg p-3 ${currentResult.correct ? "bg-green-50" : "bg-red-50"}`}>
            {currentResult.correct ? (
              <CheckCircle className="h-5 w-5 text-green-600 shrink-0" />
            ) : (
              <XCircle className="h-5 w-5 text-red-600 shrink-0" />
            )}
            <div className="text-sm">
              {!currentResult.correct && (
                <p>正确答案: {String(currentResult.correct_answer)}</p>
              )}
              {currentResult.explanation && <p className="mt-1 text-slate-600">{currentResult.explanation}</p>}
            </div>
          </div>
        )}
      </Card>

      <div className="flex justify-between">
        <Button variant="outline" disabled={currentIdx === 0} onClick={() => setCurrentIdx((i) => i - 1)}>
          上一题
        </Button>
        {!currentResult ? (
          <Button onClick={handleNext} disabled={!answers[current.id] || submitOne.isPending}>
            {submitOne.isPending ? "提交中..." : currentIdx === exercises.length - 1 ? "完成" : "下一题"}
          </Button>
        ) : (
          <Button onClick={() => currentIdx < exercises.length - 1 && setCurrentIdx((i) => i + 1)}>
            {currentIdx === exercises.length - 1 ? "查看结果" : "下一题"}
          </Button>
        )}
      </div>
    </div>
  );
}
