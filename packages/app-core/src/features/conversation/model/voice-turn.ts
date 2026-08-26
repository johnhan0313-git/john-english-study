/** Voice turn workflow as a single discriminated state. */

export type VoiceTurnPhase =
  | { kind: "idle" }
  | { kind: "recording" }
  | { kind: "processing" }
  | { kind: "playing" }
  | { kind: "error"; message: string };

export function voicePhaseFlags(phase: VoiceTurnPhase) {
  return {
    recording: phase.kind === "recording",
    processing: phase.kind === "processing",
    playing: phase.kind === "playing",
    error: phase.kind === "error" ? phase.message : null,
  };
}

export const voiceCopy = {
  playFailed: "语音播放失败",
  ttsUnavailable: "语音合成未配置或暂时不可用",
} as const;
