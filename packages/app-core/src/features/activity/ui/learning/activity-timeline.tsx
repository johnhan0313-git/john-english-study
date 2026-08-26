import { PlatformLink as Link } from "../../../../app-chrome/platform-link";
import {
  CheckCircle2,
  MessageCircle,
  MessageSquarePlus,
  Sparkles,
} from "lucide-react";
import type { ActivityTimelineItem } from "@sceneenglish/api-client/types";
import { Badge, Card } from "../../../../app-chrome/ui";
import { formatRelativeTime } from "@sceneenglish/api-client";

interface ActivityTimelineProps {
  items: ActivityTimelineItem[];
}

const TYPE_META: Record<
  ActivityTimelineItem["type"],
  { icon: typeof Sparkles; label: string; color: string }
> = {
  scenario_created: { icon: Sparkles, label: "生成场景", color: "text-brand-600 bg-brand-50" },
  scenario_completed: { icon: CheckCircle2, label: "完成练习", color: "text-emerald-600 bg-emerald-50" },
  conversation_started: { icon: MessageSquarePlus, label: "开始对话", color: "text-brand-600 bg-brand-50" },
  conversation_ended: { icon: MessageCircle, label: "结束对话", color: "text-slate-600 bg-slate-100" },
};

function timelineHref(item: ActivityTimelineItem): string {
  switch (item.type) {
    case "scenario_created":
    case "scenario_completed":
      return `/scenarios/${item.scenario.id}`;
    case "conversation_started":
    case "conversation_ended":
      return `/chat/${item.conversation.id}`;
  }
}

function timelineTitle(item: ActivityTimelineItem): string {
  switch (item.type) {
    case "scenario_created":
    case "scenario_completed":
      return item.scenario.title;
    case "conversation_started":
    case "conversation_ended":
      return item.conversation.title;
  }
}

export function ActivityTimeline({ items }: ActivityTimelineProps) {
  if (items.length === 0) {
    return (
      <Card className="py-10 text-center text-sm text-slate-500">
        暂无学习动态，开始生成场景或对话吧
      </Card>
    );
  }

  return (
    <div className="relative space-y-4 pl-6">
      <div className="absolute bottom-2 left-[11px] top-2 w-px bg-surface-border" />
      {items.map((item, idx) => {
        const meta = TYPE_META[item.type];
        const Icon = meta.icon;
        return (
          <div key={`${item.type}-${item.at}-${idx}`} className="relative">
            <div
              className={`absolute -left-6 flex h-6 w-6 items-center justify-center rounded-full ${meta.color}`}
            >
              <Icon className="h-3.5 w-3.5" />
            </div>
            <Link href={timelineHref(item)}>
              <Card hover className="ml-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{meta.label}</Badge>
                  <span className="text-xs text-slate-400">{formatRelativeTime(item.at)}</span>
                  {item.type === "scenario_completed" && (
                    <Badge variant="success">得分 {Math.round(item.score * 100)}%</Badge>
                  )}
                </div>
                <h3 className="mt-2 font-semibold text-slate-900">{timelineTitle(item)}</h3>
              </Card>
            </Link>
          </div>
        );
      })}
    </div>
  );
}
