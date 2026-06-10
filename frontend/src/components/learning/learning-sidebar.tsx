import Link from "next/link";
import { MessageCircle, Sparkles } from "lucide-react";
import type { ActivityOverview } from "@/lib/api/types";
import { Button, Card, SectionTitle } from "@/components/ui";
import { LearningHeatmap } from "./learning-heatmap";

interface LearningSidebarProps {
  overview?: ActivityOverview;
  mobile?: boolean;
}

export function LearningSidebar({ overview, mobile = false }: LearningSidebarProps) {
  const themeCounts = overview?.theme_counts ?? {};
  const themes = Object.entries(themeCounts).sort((a, b) => b[1] - a[1]);

  return (
    <aside className={mobile ? "space-y-4 lg:hidden" : "hidden space-y-4 lg:block"}>
      {overview?.heatmap && overview.heatmap.length > 0 && (
        <LearningHeatmap data={overview.heatmap} compact={mobile} />
      )}

      {themes.length > 0 && (
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

      <Card>
        <SectionTitle title="快捷操作" />
        <div className="mt-3 flex flex-col gap-2">
          <Link href="/generate">
            <Button variant="outline" size="sm" className="w-full justify-start">
              <Sparkles className="mr-2 h-4 w-4" />
              生成场景
            </Button>
          </Link>
          <Link href="/chat/new">
            <Button variant="outline" size="sm" className="w-full justify-start">
              <MessageCircle className="mr-2 h-4 w-4" />
              开始新对话
            </Button>
          </Link>
        </div>
      </Card>
    </aside>
  );
}
