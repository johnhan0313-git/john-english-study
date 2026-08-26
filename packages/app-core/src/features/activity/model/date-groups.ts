export type DateGroupKey = "today" | "yesterday" | "this_week" | "earlier";

export const DATE_GROUP_LABELS: Record<DateGroupKey, string> = {
  today: "今天",
  yesterday: "昨天",
  this_week: "本周",
  earlier: "更早",
};

const GROUP_ORDER: DateGroupKey[] = ["today", "yesterday", "this_week", "earlier"];

function startOfDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function startOfWeek(d: Date) {
  const day = d.getDay();
  const diff = day === 0 ? 6 : day - 1;
  const monday = new Date(d);
  monday.setDate(d.getDate() - diff);
  return startOfDay(monday);
}

export function getDateGroup(dateStr: string, now = new Date()): DateGroupKey {
  const date = startOfDay(new Date(dateStr));
  const today = startOfDay(now);
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);
  const weekStart = startOfWeek(now);

  if (date.getTime() === today.getTime()) return "today";
  if (date.getTime() === yesterday.getTime()) return "yesterday";
  if (date >= weekStart) return "this_week";
  return "earlier";
}

export interface DateGroup<T> {
  key: DateGroupKey;
  label: string;
  items: T[];
}

export function groupByDate<T>(items: T[], getDate: (item: T) => string): DateGroup<T>[] {
  const buckets = new Map<DateGroupKey, T[]>();
  for (const item of items) {
    const key = getDateGroup(getDate(item));
    const list = buckets.get(key) ?? [];
    list.push(item);
    buckets.set(key, list);
  }
  return GROUP_ORDER.filter((key) => buckets.has(key)).map((key) => ({
    key,
    label: DATE_GROUP_LABELS[key],
    items: buckets.get(key)!,
  }));
}
