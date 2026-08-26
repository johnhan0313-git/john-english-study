/** Home feature user-visible copy. */

export const homeCopy = {
  heroEyebrow: "今天，从一个真实场景开始",
  heroTitle: "让英语进入你的日常",
  heroDescription: "用熟悉的生活与工作语境，串联词汇、听力、表达和复习。",
  startChat: "开始对话",
  loginToStart: "登录开始",
  guestHintPrefix: "后可查看学习进度、今日场景与对话记录。词库与参考内容可匿名浏览。",
  login: "登录",
  progressTitle: "学习进度",
  progressDetail: "查看详情",
  streakLabel: "连续学习",
  streakSuffix: "天",
  dueReviewLabel: "待复习",
  masteredLabel: "已掌握",
  masteryRateLabel: "掌握率",
  dailySectionTitle: "今日场景",
  refresh: "刷新",
  loginForDailyTitle: "登录查看今日场景",
  loginForDailyDescription: "每日场景会根据你的学习进度自动生成",
  loadingDaily: "正在加载今日场景...",
  startLearning: "开始学习",
  noDailyTitle: "还没有今日场景",
  noDailyDescription: "点击下方按钮，AI 会根据你的学习进度生成专属场景",
  goToScenarios: "去场景页",
} as const;

export const dailyKindLabel: Record<string, string> = {
  review: "复习场景",
  new: "新词场景",
  challenge: "挑战场景",
};
