/** Exercise practice workflow model — pure transitions for quiz UI. */

export type PracticePhase = "answering" | "feedback" | "summary";

export interface PracticeState {
  currentIdx: number;
  answers: Record<number, string>;
  results: Record<number, { correct: boolean; correct_answer: string | string[]; explanation?: string }>;
  finished: boolean;
}

export const practiceCopy = {
  empty: "暂无练习题",
  correct: "回答正确",
  incorrect: "回答错误",
  yourAnswer: "你的答案：",
  correctAnswer: "正确答案：",
  progressSubmitted: (submitted: number, total: number) => `已提交 ${submitted} / ${total} 题`,
  questionIndex: (idx: number, total: number) => `第 ${idx + 1} / ${total} 题`,
  singleChoice: "单选题",
  fillBlank: "填空题",
} as const;

export function canSubmitAnswer(state: PracticeState, exerciseId: number, answer: string): boolean {
  return Boolean(answer.trim()) && !state.results[exerciseId];
}

export function nextIndexAfterContinue(currentIdx: number, total: number): number | "finish" {
  return currentIdx >= total - 1 ? "finish" : currentIdx + 1;
}

export function scoreFromResults(results: PracticeState["results"], total: number) {
  const correct = Object.values(results).filter((r) => r.correct).length;
  return {
    score: total ? Math.round((correct / total) * 100) : 0,
    correct,
    total,
  };
}
