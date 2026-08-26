import { describe, expect, it } from "vitest";
import {
  canSubmitAnswer,
  nextIndexAfterContinue,
  scoreFromResults,
  type PracticeState,
} from "./practice";

describe("practice model", () => {
  const empty: PracticeState = { currentIdx: 0, answers: {}, results: {}, finished: false };

  it("canSubmitAnswer requires non-empty unanswered", () => {
    expect(canSubmitAnswer(empty, 1, "  ")).toBe(false);
    expect(canSubmitAnswer(empty, 1, "A")).toBe(true);
    expect(
      canSubmitAnswer(
        { ...empty, results: { 1: { correct: true, correct_answer: "A" } } },
        1,
        "A",
      ),
    ).toBe(false);
  });

  it("nextIndexAfterContinue finishes at last", () => {
    expect(nextIndexAfterContinue(0, 3)).toBe(1);
    expect(nextIndexAfterContinue(2, 3)).toBe("finish");
  });

  it("scoreFromResults computes percent", () => {
    const results = {
      1: { correct: true, correct_answer: "A" },
      2: { correct: false, correct_answer: "B" },
    };
    expect(scoreFromResults(results, 2)).toEqual({ score: 50, correct: 1, total: 2 });
  });
});
