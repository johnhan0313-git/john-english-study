export function getConversationChineseHint(sceneBrief?: Record<string, unknown> | null): boolean {
  if (sceneBrief && typeof sceneBrief.show_chinese_hint === "boolean") {
    return sceneBrief.show_chinese_hint;
  }
  return true;
}
