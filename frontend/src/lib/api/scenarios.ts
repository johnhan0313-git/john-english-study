import { API_BASE, authFetch, authHeaders, request } from "./client";
import type { Exercise, ScenarioBrief, ScenarioDetail } from "./types";

export const scenariosApi = {
  generateScenario: (body: {
    theme?: string;
    level: string;
    word_ids?: number[];
    scenario_type: string;
    word_count: number;
  }) =>
    request<ScenarioDetail>("/scenarios/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getDailyScenarios: () =>
    request<{ date: string; items: ScenarioBrief[]; generated: boolean }>("/scenarios/daily"),

  listScenarios: () => request<{ items: ScenarioBrief[]; total: number }>("/scenarios"),

  getScenario: (id: number) => request<ScenarioDetail>(`/scenarios/${id}`),

  getScenarioAudioUrl: (id: number) => `${API_BASE}/scenarios/${id}/audio`,

  getExercises: (scenarioId: number) => request<Exercise[]>(`/exercises/scenario/${scenarioId}`),

  submitExercise: (exerciseId: number, answer: string | string[]) =>
    request<{ correct: boolean; correct_answer: string | string[]; explanation?: string }>(
      `/exercises/${exerciseId}/submit`,
      { method: "POST", body: JSON.stringify({ answer }) },
    ),

  submitBatch: (scenarioId: number, answers: Record<number, string | string[]>) =>
    request<{ score: number; total: number; correct: number; results: { correct: boolean }[] }>(
      `/exercises/scenario/${scenarioId}/submit`,
      { method: "POST", body: JSON.stringify({ answers }) },
    ),

  completeScenario: (scenarioId: number, total: number, correct: number) =>
    request<{ ok: boolean }>(`/scenarios/${scenarioId}/complete`, {
      method: "POST",
      body: JSON.stringify({ total, correct }),
    }),
};

export { authFetch, authHeaders };
