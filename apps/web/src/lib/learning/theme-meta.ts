import {
  Briefcase,
  Cpu,
  Globe,
  GraduationCap,
  Heart,
  Layers,
  LucideIcon,
  Sparkles,
} from "lucide-react";

export interface ThemeMeta {
  icon: LucideIcon;
  iconBg: string;
  iconColor: string;
  label?: string;
}

const THEME_MAP: Record<string, ThemeMeta> = {
  technology: { icon: Cpu, iconBg: "bg-sky-50", iconColor: "text-sky-600", label: "科技" },
  business: { icon: Briefcase, iconBg: "bg-amber-50", iconColor: "text-amber-600", label: "商务" },
  daily: { icon: Heart, iconBg: "bg-rose-50", iconColor: "text-rose-600", label: "日常" },
  travel: { icon: Globe, iconBg: "bg-teal-50", iconColor: "text-teal-600", label: "旅行" },
  education: { icon: GraduationCap, iconBg: "bg-violet-50", iconColor: "text-violet-600", label: "教育" },
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
  challenge: { icon: Sparkles, iconBg: "bg-violet-50", iconColor: "text-violet-600" },
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
