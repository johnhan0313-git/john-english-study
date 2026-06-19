import Link from "next/link";
import { MessageCircle } from "lucide-react";
import type { ConversationBrief } from "@/lib/api/types";
import { Badge, Button, Card, ProgressBar } from "@/components/ui";
import { formatRelativeTime } from "@/lib/learning/format-time";
import { cn } from "@/lib/utils";

interface ConversationCardProps {
  conversation: ConversationBrief;
  className?: string;
}

export function ConversationCard({ conversation, className }: ConversationCardProps) {
  const isActive = conversation.status === "active";
  const targetCount = conversation.target_words.length;
  const usedCount = conversation.words_used.length;
  const progress = targetCount > 0 ? usedCount : 0;

  return (
    <Card
      hover
      className={cn(
        "group",
        isActive && "border-l-4 border-brand-500",
        className,
      )}
    >
      <Link href={`/chat/${conversation.id}`} className="block">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-semibold text-slate-900 group-hover:text-brand-700">{conversation.title}</h3>
              <Badge variant={isActive ? "brand" : "default"}>{isActive ? "进行中" : "已结束"}</Badge>
              <Badge variant="outline">{conversation.level.toUpperCase()}</Badge>
            </div>
            <p className="mt-1 text-sm text-slate-500">
              {conversation.role_ai} · {conversation.turn_count} 轮 · {formatRelativeTime(conversation.created_at)}
            </p>
            {targetCount > 0 && (
              <div className="mt-3">
                <div className="mb-1 flex justify-between text-xs text-slate-500">
                  <span>目标词进度</span>
                  <span>{usedCount}/{targetCount}</span>
                </div>
                <ProgressBar value={progress} max={targetCount} />
              </div>
            )}
            {conversation.last_message && (
              <p className="mt-2 line-clamp-2 text-sm text-slate-600">{conversation.last_message}</p>
            )}
          </div>
          <MessageCircle className="h-5 w-5 shrink-0 text-brand-400" />
        </div>
      </Link>
      {conversation.scenario_id != null && (
        <Link
          href={`/scenarios/${conversation.scenario_id}`}
          className="mt-2 inline-block text-xs font-medium text-brand-600 hover:text-brand-700"
        >
          来源场景 →
        </Link>
      )}
      {isActive && (
        <div className="mt-3 border-t border-surface-border/60 pt-3">
          <Link href={`/chat/${conversation.id}`}>
            <Button variant="ghost" size="sm" className="w-full">
              继续对话
            </Button>
          </Link>
        </div>
      )}
    </Card>
  );
}
