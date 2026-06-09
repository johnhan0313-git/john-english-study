import { API_BASE } from "@/lib/env";

import { request } from "./client";
import type { Exercise, ScenarioBrief, ScenarioDetail } from "./types";

export const scenariosApi = {
  generateScenario: (body: {
    theme?: string;
    level: string;
    word_ids?: number[];
    scenario_type: string;
    device_id: string;
    word_count: number;
  }) =>
    request<ScenarioDetail>("/scenarios/generate", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  getDailyScenarios: (deviceId: string) =>
    request<{ date: string; items: ScenarioBrief[]; generated: boolean }>(
      `/scenarios/daily?device_id=${deviceId}`,
    ),

  listScenarios: (deviceId: string) =>
    request<{ items: ScenarioBrief[]; total: number }>(`/scenarios?device_id=${deviceId}`),

  getScenario: (id: number) => request<ScenarioDetail>(`/scenarios/${id}`),

  getScenarioAudioUrl: (id: number) => `${API_BASE}/scenarios/${id}/audio`,

  getExercises: (scenarioId: number) => request<Exercise[]>(`/exercises/scenario/${scenarioId}`),

  submitExercise: (exerciseId: number, answer: string | string[], deviceId: string) =>
    request<{ correct: boolean; correct_answer: string | string[]; explanation?: string }>(
      `/exercises/${exerciseId}/submit`,
      { method: "POST", body: JSON.stringify({ answer, device_id: deviceId }) },
    ),

  submitBatch: (scenarioId: number, answers: Record<number, string | string[]>, deviceId: string) =>
    request<{ score: number; total: number; correct: number; results: { correct: boolean }[] }>(
      `/exercises/scenario/${scenarioId}/submit`,
      { method: "POST", body: JSON.stringify({ answers, device_id: deviceId }) },
    ),
};
