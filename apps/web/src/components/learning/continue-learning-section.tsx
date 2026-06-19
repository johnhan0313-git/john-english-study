import Link from "next/link";
import { ArrowRight, Layers, MessageCircle } from "lucide-react";
import type { ActivityOverview } from "@/lib/api/types";
import { SectionTitle } from "@/components/ui";
import { ConversationCard } from "./conversation-card";
import { ScenarioGridCard } from "./scenario-grid-card";

interface ContinueLearningSectionProps {
  overview?: ActivityOverview;
}

export function ContinueLearningSection({ overview }: ContinueLearningSectionProps) {
  const active = overview?.continue?.active_conversations ?? [];
  const incomplete = overview?.continue?.incomplete_scenarios ?? [];

  if (active.length === 0 && incomplete.length === 0) return null;

  return (
    <section className="space-y-4">
      <SectionTitle title="继续学习" />
      {active.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
            <MessageCircle className="h-4 w-4 text-brand-500" />
            进行中的对话
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            {active.map((c) => (
              <ConversationCard key={c.id} conversation={c} />
            ))}
          </div>
        </div>
      )}
      {incomplete.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-sm font-medium text-slate-600">
              <Layers className="h-4 w-4 text-brand-500" />
              待完成场景
            </div>
            <Link href="/activity?tab=scenarios" className="text-xs font-medium text-brand-600 hover:text-brand-700">
              查看全部
              <ArrowRight className="ml-0.5 inline h-3 w-3" />
            </Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {incomplete.map((s) => (
              <ScenarioGridCard key={s.id} scenario={s} />
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
