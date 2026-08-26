import { PlatformLink as Link } from "../../../../app-chrome/platform-link";
import { ArrowRight } from "lucide-react";
import type { ScenarioBrief } from "@sceneenglish/api-client/types";
import { Badge, Card } from "../../../../app-chrome/ui";
import { getThemeLabel, getThemeMeta, scenarioTypeLabel } from "../../model";
import { cn } from "../../../../app-chrome/utils";

interface ScenarioGridCardProps {
  scenario: ScenarioBrief;
  href?: string;
  className?: string;
}

export function ScenarioGridCard({ scenario, href, className }: ScenarioGridCardProps) {
  const meta = getThemeMeta(scenario.theme, scenario.daily_kind);
  const Icon = meta.icon;
  const themeLabel = getThemeLabel(scenario.theme, scenario.daily_kind);
  const link = href ?? `/scenarios/${scenario.id}`;

  return (
    <Link href={link} className={cn("block", className)}>
      <Card hover className="group h-full">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-xl", meta.iconBg, meta.iconColor)}>
              <Icon className="h-4 w-4" />
            </div>
            <Badge variant="outline">{themeLabel}</Badge>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-1">
            {scenario.is_daily && <Badge variant="success">每日</Badge>}
            <Badge variant="outline">{scenario.level.toUpperCase()}</Badge>
          </div>
        </div>

        <h3 className="mt-4 line-clamp-2 text-lg font-bold text-slate-900 transition-colors group-hover:text-brand-700">
          {scenario.title}
        </h3>

        {scenario.summary_preview && (
          <p className="mt-2 line-clamp-2 text-sm text-slate-500">{scenario.summary_preview}</p>
        )}

        <p className="mt-2 text-sm text-slate-500">
          {scenarioTypeLabel[scenario.scenario_type] ?? scenario.scenario_type} · {scenario.word_count} 词
          {scenario.exercise_count != null && scenario.exercise_count > 0 && ` · ${scenario.exercise_count} 练习`}
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {scenario.is_completed && <Badge variant="success">已完成</Badge>}
          {scenario.best_score != null && (
            <Badge variant="brand">得分 {Math.round(scenario.best_score * 100)}%</Badge>
          )}
          {(scenario.conversation_count ?? 0) > 0 && (
            <Badge variant="default">{scenario.conversation_count} 次对话</Badge>
          )}
        </div>

        <div className="mt-5 flex items-center text-sm font-semibold text-brand-600">
          开始学习
          <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
        </div>
      </Card>
    </Link>
  );
}
