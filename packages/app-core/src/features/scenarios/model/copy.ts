export const scenarioDetailCopy = {
  listenHint: "听完音频后，进入练习页完成听力理解题",
  listenMode: "听力模式 · 先听再理解",
  speakMode: "跟读模式",
  startRecord: "开始录音",
  stopRecord: "停止并评测",
  play: "播放",
  pause: "暂停",
  tabHints: {
    read: "点击正文高亮词或上方标签查看释义",
    listen: "建议先完整听一遍，再切回阅读对照原文",
    speak: "跟读句子中包含场景核心词汇",
    write: "写作时尽量自然运用标亮的目标词",
  },
} as const;

export type ScenarioDetailTab = "read" | "listen" | "speak" | "write" | "chat";
