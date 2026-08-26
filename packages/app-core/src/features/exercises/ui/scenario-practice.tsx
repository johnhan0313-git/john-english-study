"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useParams } from "../../../platform/context";
import { useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import { api, Exercise } from "@sceneenglish/api-client";
import { RequireAuth } from "../../auth/ui/require-auth";
import { Badge, Button, Card, Input, ProgressBar, Spinner } from "../../../app-chrome/ui";
import { cn } from "../../../app-chrome/utils";

type ExerciseResult = {
  correct: boolean;
  correct_answer: string | string[];
  explanation?: string;
};

function formatAnswer(exercise: Exercise, answer: string | string[]) {
  if (exercise.type === "single_choice" && typeof answer === "string") {
    const option = exercise.payload.options?.find((opt) => opt.label === answer);
    return option ? `${answer}. ${option.text}` : answer;
  }
  if (Array.isArray(answer)) return answer.join(" / ");
  return answer;
}

function ExerciseFeedback({
  exercise,
  userAnswer,
  result,
}: {
  exercise: Exercise;
  userAnswer: string;
  result: ExerciseResult;
}) {
  return (
    <div
      className={cn(
        "mt-4 flex items-start gap-2 rounded-xl p-4",
        result.correct ? "bg-emerald-50 ring-1 ring-emerald-200" : "bg-red-50 ring-1 ring-red-200",
      )}
    >
      {result.correct ? (
        <CheckCircle className="h-5 w-5 shrink-0 text-emerald-600" />
      ) : (
        <XCircle className="h-5 w-5 shrink-0 text-red-600" />
      )}
      <div className="min-w-0 text-sm">
        <p className={cn("font-semibold", result.correct ? "text-emerald-800" : "text-red-800")}>
          {result.correct ? "回答正确" : "回答错误"}
        </p>
        {!result.correct && (
          <p className="mt-1 text-slate-700">
            你的答案：{formatAnswer(exercise, userAnswer)}
          </p>
        )}
        {!result.correct && (
          <p className="mt-0.5 text-slate-700">
            正确答案：{formatAnswer(exercise, result.correct_answer)}
          </p>
        )}
        {result.explanation && <p className="mt-2 text-slate-600">{result.explanation}</p>}
      </div>
    </div>
  );
}

function ExerciseItem({
  exercise,
  answer,
  onChange,
  result,
}: {
  exercise: Exercise;
  answer: string;
  onChange: (val: string) => void;
  result?: ExerciseResult;
}) {
  if (exercise.type === "single_choice") {
    return (
      <div className="space-y-3">
        <p className="font-medium">{exercise.payload.question}</p>
        <div className="space-y-2">
          {exercise.payload.options?.map((opt) => (
            <label
              key={opt.label}
              className={cn(
                "flex items-center gap-3 rounded-xl border p-3.5 transition-all",
                !result && "cursor-pointer hover:border-brand-200 hover:bg-white",
                !result && answer === opt.label && "border-brand-400 bg-brand-50 shadow-sm",
                !result && answer !== opt.label && "border-surface-border",
                result && result.correct_answer === opt.label && "border-emerald-400 bg-emerald-50",
                result && answer === opt.label && !result.correct && "border-red-400 bg-red-50",
                result && answer !== opt.label && result.correct_answer !== opt.label && "border-surface-border opacity-60",
              )}
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
        <p className="reading-text text-slate-700">{exercise.payload.passage_with_blanks}</p>
        <Input
          value={answer}
          onChange={(e) => onChange(e.target.value)}
          disabled={!!result}
          placeholder="填入答案..."
        />
      </div>
    );
  }

  return null;
}

function PracticeSummary({
  exercises,
  answers,
  results,
  batchScore,
  scenarioId,
}: {
  exercises: Exercise[];
  answers: Record<number, string>;
  results: Record<number, ExerciseResult>;
  batchScore: { score: number; correct: number; total: number };
  scenarioId: string;
}) {
  const wrongItems = exercises.filter((ex) => results[ex.id] && !results[ex.id].correct);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card className="text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100">
          <CheckCircle className="h-10 w-10 text-emerald-600" />
        </div>
        <h2 className="mt-4 text-2xl font-bold text-slate-900">练习完成</h2>
        <p className="mt-2 text-5xl font-bold text-gradient">{batchScore.score}</p>
        <p className="text-slate-600">正确 {batchScore.correct} / {batchScore.total} 题</p>
        <div className="mt-6 flex justify-center gap-3">
          <Link href={`/scenarios/${scenarioId}`}>
            <Button variant="outline">返回场景</Button>
          </Link>
          <Link href="/">
            <Button>回首页</Button>
          </Link>
        </div>
      </Card>

      {wrongItems.length > 0 && (
        <Card className="space-y-4">
          <h3 className="font-semibold text-slate-900">错题回顾（{wrongItems.length} 题）</h3>
          <div className="space-y-4">
            {wrongItems.map((ex, idx) => {
              const result = results[ex.id];
              const userAnswer = answers[ex.id] || "";
              return (
                <div key={ex.id} className="rounded-xl border border-red-100 bg-red-50/40 p-4">
                  <p className="text-xs font-medium text-red-600">错题 {idx + 1}</p>
                  <p className="mt-1 font-medium text-slate-900">
                    {ex.payload.question || "填空题"}
                  </p>
                  <p className="mt-2 text-sm text-slate-700">
                    你的答案：{formatAnswer(ex, userAnswer)}
                  </p>
                  <p className="mt-0.5 text-sm text-slate-700">
                    正确答案：{formatAnswer(ex, result.correct_answer)}
                  </p>
                  {result.explanation && (
                    <p className="mt-2 text-sm text-slate-600">{result.explanation}</p>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}
    </div>
  );
}

function PracticeContent() {
  const { id } = useParams<{ id: string }>();
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [results, setResults] = useState<Record<number, ExerciseResult>>({});
  const [finished, setFinished] = useState(false);
  const [batchScore, setBatchScore] = useState<{ score: number; correct: number; total: number } | null>(null);

  const { data: exercises, isLoading } = useQuery({
    queryKey: ["exercises", id],
    queryFn: () => api.getExercises(Number(id)),
  });

  const submitOne = useMutation({
    mutationFn: ({ exerciseId, answer }: { exerciseId: number; answer: string }) =>
      api.submitExercise(exerciseId, answer),
    onSuccess: (data, vars) => {
      setResults((prev) => ({ ...prev, [vars.exerciseId]: data }));
    },
  });

  const handleSubmit = async () => {
    if (!exercises) return;
    const ex = exercises[currentIdx];
    const answer = answers[ex.id]?.trim() || "";
    if (!answer || results[ex.id]) return;
    await submitOne.mutateAsync({ exerciseId: ex.id, answer });
  };

  const handleContinue = async () => {
    if (!exercises) return;
    const isLast = currentIdx >= exercises.length - 1;

    if (isLast) {
      const correct = Object.values(results).filter((r) => r.correct).length;
      setBatchScore({
        score: Math.round((correct / exercises.length) * 100),
        correct,
        total: exercises.length,
      });
      setFinished(true);
      await api.completeScenario(Number(id), exercises.length, correct);
      return;
    }

    setCurrentIdx((i) => i + 1);
  };

  if (isLoading) return <Spinner />;
  if (!exercises?.length) return <Card>暂无练习题</Card>;

  if (finished && batchScore) {
    return (
      <PracticeSummary
        exercises={exercises}
        answers={answers}
        results={results}
        batchScore={batchScore}
        scenarioId={id}
      />
    );
  }

  const current = exercises[currentIdx];
  const currentResult = results[current.id];
  const submittedCount = Object.keys(results).length;
  const progress = (submittedCount / exercises.length) * 100;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <div className="flex items-center justify-between text-sm text-slate-500">
          <span>第 {currentIdx + 1} / {exercises.length} 题</span>
          <Badge>{current.type === "single_choice" ? "单选题" : "填空题"}</Badge>
        </div>
        <ProgressBar value={progress} className="mt-2" />
        <p className="mt-1 text-xs text-slate-400">已提交 {submittedCount} / {exercises.length} 题</p>
      </div>

      <Card>
        <ExerciseItem
          exercise={current}
          answer={answers[current.id] || ""}
          onChange={(val) => setAnswers((prev) => ({ ...prev, [current.id]: val }))}
          result={currentResult}
        />

        {currentResult && (
          <ExerciseFeedback
            exercise={current}
            userAnswer={answers[current.id] || ""}
            result={currentResult}
          />
        )}
      </Card>

      <div className="flex justify-between gap-3">
        <Button
          variant="outline"
          disabled={currentIdx === 0 || submitOne.isPending}
          onClick={() => setCurrentIdx((i) => i - 1)}
        >
          上一题
        </Button>

        {!currentResult ? (
          <Button
            onClick={handleSubmit}
            disabled={!answers[current.id]?.trim() || submitOne.isPending}
          >
            {submitOne.isPending ? "提交中..." : "提交答案"}
          </Button>
        ) : (
          <Button onClick={handleContinue}>
            {currentIdx === exercises.length - 1 ? "查看结果" : "下一题"}
          </Button>
        )}
      </div>
    </div>
  );
}

export default function PracticePage() {
  return (
    <RequireAuth>
      <PracticeContent />
    </RequireAuth>
  );
}
