/** Activity feature user-visible empty / error / load-more copy. */

export const activityCopy = {
  loadingScenarios: "加载场景...",
  loadingConversations: "加载对话...",
  loadingTimeline: "加载动态...",
  loadingStats: "加载统计...",
  loadMore: "加载更多",
  loadingMore: "加载中...",

  scenariosLoadFailedTitle: "场景加载失败",
  scenariosLoadFailedDescription: "请确认后端已启动并已登录",
  scenariosEmptyTitle: "暂无场景",
  scenariosEmptyDescription: "去首页获取今日场景，或生成一个自定义场景",
  scenariosEmptyAction: "生成场景",
  scenariosNoMatchTitle: "无匹配场景",
  scenariosNoMatchDescription: "试试调整筛选条件",

  conversationsLoadFailedTitle: "对话加载失败",
  conversationsLoadFailedDescription: "请确认后端已启动并已登录",
  conversationsEmptyTitle: "还没有对话记录",
  conversationsEmptyDescription: "创建一个新对话，开始 1v1 场景角色扮演练习",
  conversationsEmptyAction: "开始新对话",
  conversationsNoMatchTitle: "无匹配对话",
  conversationsNoMatchDescription: "试试调整筛选条件",
  conversationsActiveSection: "进行中",

  timelineLoadFailedTitle: "动态加载失败",
  timelineLoadFailedDescription: "请确认后端已更新并已登录",
} as const;
