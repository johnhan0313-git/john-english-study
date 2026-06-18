import type { ActivityOverview } from "@/lib/api/types";
import { Card, SectionTitle } from "@/components/ui";
import { LearningHeatmap } from "./learning-heatmap";

interface LearningSidebarProps {
  overview?: ActivityOverview;
  mobile?: boolean;
}

export function LearningSidebar({ overview, mobile = false }: LearningSidebarProps) {
  const themeCounts = overview?.theme_counts ?? {};
  const themes = Object.entries(themeCounts).sort((a, b) => b[1] - a[1]);
  const hasHeatmap = Boolean(overview?.heatmap?.length);
  const hasThemes = themes.length > 0;

  if (!hasHeatmap && !hasThemes) return null;

  return (
    <aside className={mobile ? "space-y-4 lg:hidden" : "hidden space-y-4 lg:block"}>
      {hasHeatmap && overview?.heatmap && (
        <LearningHeatmap data={overview.heatmap} compact={mobile} />
      )}

      {hasThemes && (
        <Card>
          <SectionTitle title="主题分布" />
          <ul className="mt-3 space-y-2">
            {themes.map(([theme, count]) => (
              <li key={theme} className="flex items-center justify-between text-sm">
                <span className="capitalize text-slate-700">{theme}</span>
                <span className="font-semibold text-slate-500">{count}</span>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </aside>
  );
}
