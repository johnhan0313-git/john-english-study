export const scenarioDetailCopy = {
  listenHint: "听完音频后，进入练习页完成听力理解题",
  listenMode: "听力模式 · 先听再理解",
  speakMode: "跟读模式",
  startRecord: "开始录音",
  stopRecord: "停止并评测",
  play: "播放",
  pause: "暂停",
} as const;

export type ScenarioDetailTab = "read" | "listen" | "speak" | "write" | "chat";
