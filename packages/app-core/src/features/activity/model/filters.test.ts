import { describe, expect, it } from "vitest";
import {
  EMPTY_SCENARIO_FILTERS,
  filterScenarios,
  parseScenarioFiltersFromSearch,
  type ScenarioFilters,
} from "./filters";

describe("activity filters", () => {
  const items = [
    { id: 1, level: "cet4", theme: "travel", is_daily: true, scenario_type: "narrative" },
    { id: 2, level: "cet6", theme: "work", is_daily: false, scenario_type: "dialogue" },
  ] as any;

  it("returns all when empty", () => {
    expect(filterScenarios(items, EMPTY_SCENARIO_FILTERS)).toHaveLength(2);
  });

  it("filters by level and kind", () => {
    const filters: ScenarioFilters = {
      levels: ["cet4"],
      themes: [],
      scenarioKind: "daily",
    };
    expect(filterScenarios(items, filters).map((s) => s.id)).toEqual([1]);
  });

  it("parses search params", () => {
    const params = new URLSearchParams("level=cet4&kind=dialogue");
    expect(parseScenarioFiltersFromSearch(params)).toEqual({
      levels: ["cet4"],
      themes: [],
      scenarioKind: "dialogue",
    });
  });
});
