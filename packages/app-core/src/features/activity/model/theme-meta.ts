import {
  Briefcase,
  Brain,
  Cpu,
  FlaskConical,
  Globe,
  GraduationCap,
  Heart,
  Layers,
  LucideIcon,
  Newspaper,
  Sparkles,
  UtensilsCrossed,
  Users,
  Dumbbell,
} from "lucide-react";

export interface ThemeMeta {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  label?: string;
}

const THEME_MAP: Record<string, ThemeMeta> = {
  technology: { icon: Cpu, iconBg: "bg-orange-50", iconColor: "text-orange-700", label: "科技" },
  business: { icon: Briefcase, iconBg: "bg-amber-50", iconColor: "text-amber-700", label: "商务" },
  daily: { icon: Heart, iconBg: "bg-rose-50", iconColor: "text-rose-600", label: "日常" },
  travel: { icon: Globe, iconBg: "bg-amber-50", iconColor: "text-amber-700", label: "旅行" },
  campus: { icon: GraduationCap, iconBg: "bg-brand-50", iconColor: "text-brand-700", label: "校园" },
  education: { icon: GraduationCap, iconBg: "bg-brand-50", iconColor: "text-brand-700", label: "教育" },
  health: { icon: Heart, iconBg: "bg-red-50", iconColor: "text-red-600", label: "健康" },
  environment: { icon: Globe, iconBg: "bg-lime-50", iconColor: "text-lime-700", label: "环境" },
  culture: { icon: Layers, iconBg: "bg-orange-50", iconColor: "text-orange-700", label: "文化" },
  food: { icon: UtensilsCrossed, iconBg: "bg-orange-50", iconColor: "text-orange-600", label: "美食" },
  sports: { icon: Dumbbell, iconBg: "bg-amber-50", iconColor: "text-amber-800", label: "运动" },
  social: { icon: Users, iconBg: "bg-rose-50", iconColor: "text-rose-600", label: "社交" },
  news: { icon: Newspaper, iconBg: "bg-stone-100", iconColor: "text-stone-700", label: "新闻" },
  psychology: { icon: Brain, iconBg: "bg-rose-50", iconColor: "text-rose-700", label: "心理" },
  science: { icon: FlaskConical, iconBg: "bg-yellow-50", iconColor: "text-yellow-700", label: "科学" },
  general: { icon: Layers, iconBg: "bg-brand-50", iconColor: "text-brand-600" },
};

const dailyKindLabel: Record<string, string> = {
  review: "复习场景",
  new: "新词场景",
  challenge: "挑战场景",
};

const dailyKindVariant: Record<string, ThemeMeta> = {
  review: { icon: Sparkles, iconBg: "bg-amber-50", iconColor: "text-amber-600" },
  new: { icon: Sparkles, iconBg: "bg-brand-50", iconColor: "text-brand-600" },
  challenge: { icon: Sparkles, iconBg: "bg-amber-50", iconColor: "text-amber-700" },
};

export function getThemeMeta(theme: string, dailyKind?: string | null): ThemeMeta {
  if (dailyKind && dailyKindVariant[dailyKind]) {
    return dailyKindVariant[dailyKind];
  }
  const key = theme.toLowerCase();
  return THEME_MAP[key] ?? THEME_MAP.general;
}

export function getThemeLabel(theme: string, dailyKind?: string | null): string {
  if (dailyKind && dailyKindLabel[dailyKind]) {
    return dailyKindLabel[dailyKind];
  }
  const key = theme.toLowerCase();
  return THEME_MAP[key]?.label ?? theme;
}

export const scenarioTypeLabel: Record<string, string> = {
  narrative: "阅读",
  dialogue: "对话",
};
