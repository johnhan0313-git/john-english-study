import { describe, expect, it } from "vitest";
import { voicePhaseFlags, type VoiceTurnPhase } from "./voice-turn";

describe("voicePhaseFlags", () => {
  const cases: Array<[VoiceTurnPhase, { recording: boolean; processing: boolean; playing: boolean; error: string | null }]> = [
    [{ kind: "idle" }, { recording: false, processing: false, playing: false, error: null }],
    [{ kind: "recording" }, { recording: true, processing: false, playing: false, error: null }],
    [{ kind: "processing" }, { recording: false, processing: true, playing: false, error: null }],
    [{ kind: "playing" }, { recording: false, processing: false, playing: true, error: null }],
    [{ kind: "error", message: "x" }, { recording: false, processing: false, playing: false, error: "x" }],
  ];

  it.each(cases)("%j", (phase, expected) => {
    expect(voicePhaseFlags(phase)).toEqual(expected);
  });
});
