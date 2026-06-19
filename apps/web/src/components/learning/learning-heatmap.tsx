import { useMemo, useState } from "react";
import type { HeatmapDay } from "@/lib/api/types";
import { Card, SectionTitle } from "@/components/ui";
import { cn } from "@/lib/utils";

interface LearningHeatmapProps {
  data: HeatmapDay[];
  weeks?: number;
  compact?: boolean;
}

function buildGrid(data: HeatmapDay[], weeks: number) {
  const map = new Map(data.map((d) => [d.date, d.count]));
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const cells: { date: string; count: number; label: string }[] = [];
  const totalDays = weeks * 7;

  for (let i = totalDays - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(today.getDate() - i);
    const key = d.toISOString().slice(0, 10);
    cells.push({
      date: key,
      count: map.get(key) ?? 0,
      label: d.toLocaleDateString("zh-CN"),
    });
  }
  return cells;
}

function intensityClass(count: number): string {
  if (count === 0) return "bg-slate-100";
  if (count === 1) return "bg-brand-200";
  if (count <= 3) return "bg-brand-400";
  return "bg-brand-600";
}

export function LearningHeatmap({ data, weeks = 12, compact = false }: LearningHeatmapProps) {
  const [hovered, setHovered] = useState<{ date: string; count: number; label: string } | null>(null);
  const cells = useMemo(() => buildGrid(data, weeks), [data, weeks]);
  const maxCount = Math.max(...cells.map((c) => c.count), 1);

  return (
    <Card className={cn(compact ? "p-4" : "p-5")}>
      <SectionTitle title="学习热力图" />
      <p className="mb-3 text-xs text-slate-500">最近 {weeks} 周 · 场景、对话与练习活动</p>
      <div
        className="grid gap-1"
        style={{ gridTemplateColumns: `repeat(${weeks}, minmax(0, 1fr))` }}
        onMouseLeave={() => setHovered(null)}
      >
        {Array.from({ length: weeks }, (_, weekIdx) => (
          <div key={weekIdx} className="flex flex-col gap-1">
            {cells.slice(weekIdx * 7, weekIdx * 7 + 7).map((cell) => (
              <div
                key={cell.date}
                title={`${cell.label}: ${cell.count} 次活动`}
                className={cn(
                  "aspect-square min-h-[10px] rounded-sm transition-colors",
                  intensityClass(cell.count),
                  cell.count >= maxCount && cell.count > 0 && "ring-1 ring-brand-700/30",
                )}
                onMouseEnter={() => setHovered(cell)}
              />
            ))}
          </div>
        ))}
      </div>
      {hovered && (
        <p className="mt-2 text-xs text-slate-600">
          {hovered.label}：{hovered.count} 次活动
        </p>
      )}
    </Card>
  );
}
