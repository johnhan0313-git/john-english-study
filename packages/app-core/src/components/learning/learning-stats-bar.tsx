import { Layers, MessageCircle, Sparkles, Zap } from "lucide-react";
import type { ActivityOverview } from "@sceneenglish/api-client/types";
import { StatCard } from "@sceneenglish/app-core/components/ui";
import { isThisWeek } from "@sceneenglish/api-client";
import type { ConversationBrief, ScenarioBrief } from "@sceneenglish/api-client/types";

interface LearningStatsBarProps {
  overview?: ActivityOverview;
  scenarios?: ScenarioBrief[];
  conversations?: ConversationBrief[];
  scenarioTotal?: number;
  conversationTotal?: number;
}

export function LearningStatsBar({
  overview,
  scenarios = [],
  conversations = [],
  scenarioTotal,
  conversationTotal,
}: LearningStatsBarProps) {
  const totalScenarios = overview?.scenario_total ?? scenarioTotal ?? scenarios.length;
  const totalConversations = overview?.conversation_total ?? conversationTotal ?? conversations.length;
  const scenarioThisWeek =
    overview?.scenario_this_week ?? scenarios.filter((s) => isThisWeek(s.created_at)).length;
  const activeConversations =
    overview?.conversation_active ?? conversations.filter((c) => c.status === "active").length;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard label="场景总数" value={totalScenarios} icon={Layers} tone="brand" />
      <StatCard label="本周新增场景" value={scenarioThisWeek} icon={Sparkles} tone="violet" />
      <StatCard label="对话总数" value={totalConversations} icon={MessageCircle} tone="emerald" />
      <StatCard label="进行中对话" value={activeConversations} icon={Zap} tone="amber" />
    </div>
  );
}
