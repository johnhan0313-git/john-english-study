"use client";

import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { PlatformLink as Link } from "../../../app-chrome/platform-link";
import { useNavigate, useSearchParams } from "../../../platform/context";
import { useCallback, useMemo, useState } from "react";
import { Clock, Layers, MessageCircle, Plus, Sparkles } from "lucide-react";
import { api } from "@sceneenglish/api-client";
import type { ConversationBrief, ScenarioBrief } from "@sceneenglish/api-client/types";
import { RequireAuth } from "../../auth/ui/require-auth";
import {
  ActivityTimeline,
  ContinueLearningSection,
  ConversationCard,
  DateGroupSection,
  FilterChipGroup,
  FilterPanel,
  LearningEmptyGuide,
  LearningSidebar,
  hasLearningSidebarContent,
  LearningStatsBar,
  ScenarioGridCard,
} from "./learning";
import { groupByDate } from "../model";
import {
  buildScenarioThemeOptions,
  CONVERSATION_STATUS_OPTIONS,
  LEARNING_LEVEL_OPTIONS,
  SCENARIO_KIND_OPTIONS,
} from "../model";
import {
  EMPTY_CONVERSATION_FILTERS,
  EMPTY_SCENARIO_FILTERS,
  filterConversations,
  filterScenarios,
  scenarioFiltersToSearch,
  type ScenarioKind,
} from "../model";
import {
  ACTIVITY_LIST_PAGE_SIZE,
  ACTIVITY_QUERY_KEYS,
  conversationsNextPageParam,
  normalizePage,
  scenariosNextPageParam,
  timelineNextPageParam,
} from "../model";
import { Button, EmptyState, PageHeader, Spinner, Tabs } from "../../../app-chrome/ui";
import { cn } from "../../../app-chrome/utils";

type ActivityTab = "scenarios" | "conversations" | "timeline";

const TAB_OPTIONS = [
  { id: "scenarios" as const, label: "场景", icon: Layers },
  { id: "conversations" as const, label: "对话", icon: MessageCircle },
  { id: "timeline" as const, label: "全部动态", icon: Clock },
];

function ScenariosTabContent({
  filters,
  onFiltersChange,
}: {
  filters: typeof EMPTY_SCENARIO_FILTERS;
  onFiltersChange: (filters: typeof EMPTY_SCENARIO_FILTERS) => void;
}) {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ACTIVITY_QUERY_KEYS.scenarios,
    queryFn: async ({ pageParam = 0 }) =>
      normalizePage(await api.listScenariosPage(pageParam, ACTIVITY_LIST_PAGE_SIZE)),
    getNextPageParam: scenariosNextPageParam,
    initialPageParam: 0,
  });

  const items = useMemo(
    () => data?.pages.flatMap((p) => normalizePage(p).items) ?? [],
    [data],
  );
  const filtered = useMemo(() => filterScenarios(items, filters), [items, filters]);
  const groups = useMemo(() => groupByDate(filtered, (s) => s.created_at), [filtered]);

  const { data: wordGroups } = useQuery({
    queryKey: ["groups"],
    queryFn: () => api.getWordGroups(),
  });

  const themeOptions = useMemo(() => buildScenarioThemeOptions(wordGroups), [wordGroups]);

  if (isLoading) return <Spinner label="加载场景..." />;

  if (isError) {
    return <EmptyState title="场景加载失败" description="请确认后端已启动并已登录" />;
  }

  if (!items.length) {
    return (
      <div className="space-y-6">
        <EmptyState
          title="暂无场景"
          description="去首页获取今日场景，或生成一个自定义场景"
          action={
            <Link href="/generate">
              <Button>
                <Sparkles className="mr-2 h-4 w-4" />
                生成场景
              </Button>
            </Link>
          }
        />
        <LearningEmptyGuide variant="scenarios" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <FilterPanel>
        <FilterChipGroup
          label="等级"
          options={LEARNING_LEVEL_OPTIONS}
          value={filters.levels[0] ?? null}
          onChange={(level) => onFiltersChange({ ...filters, levels: level ? [level] : [] })}
        />
        <FilterChipGroup
          label="类型"
          options={SCENARIO_KIND_OPTIONS}
          value={filters.scenarioKind}
          onChange={(kind) => onFiltersChange({ ...filters, scenarioKind: kind as ScenarioKind | null })}
        />
        <FilterChipGroup
          label="主题"
          options={themeOptions}
          value={filters.themes[0] ?? null}
          onChange={(theme) => onFiltersChange({ ...filters, themes: theme ? [theme] : [] })}
        />
      </FilterPanel>
      {filtered.length === 0 ? (
        <EmptyState title="无匹配场景" description="试试调整筛选条件" />
      ) : (
        <div className="space-y-8">
          {groups.map((group) => (
            <DateGroupSection key={group.key} label={group.label} count={group.items.length}>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3">
                {group.items.map((s) => (
                  <ScenarioGridCard key={s.id} scenario={s} />
                ))}
              </div>
            </DateGroupSection>
          ))}
        </div>
      )}
      {hasNextPage && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? "加载中..." : "加载更多"}
          </Button>
        </div>
      )}
    </div>
  );
}

function ConversationsTabContent({
  filters,
  onFiltersChange,
}: {
  filters: typeof EMPTY_CONVERSATION_FILTERS;
  onFiltersChange: (filters: typeof EMPTY_CONVERSATION_FILTERS) => void;
}) {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ACTIVITY_QUERY_KEYS.conversations,
    queryFn: async ({ pageParam = 1 }) =>
      normalizePage(await api.listConversationsPage(pageParam, ACTIVITY_LIST_PAGE_SIZE)),
    getNextPageParam: conversationsNextPageParam,
    initialPageParam: 1,
  });

  const items = useMemo(
    () => data?.pages.flatMap((p) => normalizePage(p).items) ?? [],
    [data],
  );
  const active = useMemo(() => items.filter((c) => c.status === "active"), [items]);
  const rest = useMemo(() => items.filter((c) => c.status !== "active"), [items]);
  const filteredActive = useMemo(() => filterConversations(active, filters), [active, filters]);
  const filteredRest = useMemo(() => filterConversations(rest, filters), [rest, filters]);
  const filtered = useMemo(() => [...filteredActive, ...filteredRest], [filteredActive, filteredRest]);

  const statusOptions = CONVERSATION_STATUS_OPTIONS;
  const levelOptions = LEARNING_LEVEL_OPTIONS;

  if (isLoading) return <Spinner label="加载对话..." />;

  if (isError) {
    return <EmptyState title="对话加载失败" description="请确认后端已启动并已登录" />;
  }

  if (!items.length) {
    return (
      <div className="space-y-6">
        <EmptyState
          title="还没有对话记录"
          description="创建一个新对话，开始 1v1 场景角色扮演练习"
          action={
            <Link href="/chat/new">
              <Button>开始新对话</Button>
            </Link>
          }
        />
        <LearningEmptyGuide variant="conversations" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <FilterPanel>
        <FilterChipGroup
          label="状态"
          options={statusOptions}
          value={filters.statuses[0] ?? null}
          onChange={(status) => onFiltersChange({ ...filters, statuses: status ? [status] : [] })}
        />
        <FilterChipGroup
          label="等级"
          options={levelOptions}
          value={filters.levels[0] ?? null}
          onChange={(level) => onFiltersChange({ ...filters, levels: level ? [level] : [] })}
        />
      </FilterPanel>

      {filteredActive.length > 0 && (
        <section className="space-y-3">
          <h3 className="text-sm font-bold text-brand-700">进行中</h3>
          <div className="grid gap-3 md:grid-cols-2">
            {filteredActive.map((c) => (
              <ConversationCard key={c.id} conversation={c} />
            ))}
          </div>
        </section>
      )}

      {filteredRest.length > 0 && (
        <div className="space-y-8">
          {groupByDate(filteredRest, (c) => c.created_at).map((group) => (
            <DateGroupSection key={group.key} label={group.label} count={group.items.length}>
              <div className="grid gap-3 md:grid-cols-2">
                {group.items.map((c) => (
                  <ConversationCard key={c.id} conversation={c} />
                ))}
              </div>
            </DateGroupSection>
          ))}
        </div>
      )}

      {filtered.length === 0 && <EmptyState title="无匹配对话" description="试试调整筛选条件" />}

      {hasNextPage && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? "加载中..." : "加载更多"}
          </Button>
        </div>
      )}
    </div>
  );
}

function TimelineTabContent() {
  const { data, isLoading, isError, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
    queryKey: ACTIVITY_QUERY_KEYS.timeline,
    queryFn: async ({ pageParam = 0 }) =>
      normalizePage(await api.getActivityTimeline(pageParam, ACTIVITY_LIST_PAGE_SIZE)),
    getNextPageParam: timelineNextPageParam,
    initialPageParam: 0,
  });

  const items = useMemo(() => data?.pages.flatMap((p) => normalizePage(p).items) ?? [], [data]);

  if (isLoading) return <Spinner label="加载动态..." />;

  if (isError) {
    return <EmptyState title="动态加载失败" description="请确认后端已更新并已登录" />;
  }

  return (
    <div className="space-y-4">
      <ActivityTimeline items={items} />
      {hasNextPage && (
        <div className="flex justify-center pt-2">
          <Button variant="outline" onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? "加载中..." : "加载更多"}
          </Button>
        </div>
      )}
    </div>
  );
}

function ActivityHubContent() {
  const navigate = useNavigate();
  const searchParams = useSearchParams();
  const tabParam = searchParams.get("tab");
  const activeTab: ActivityTab =
    tabParam === "conversations" || tabParam === "timeline" ? tabParam : "scenarios";

  const [scenarioFilters, setScenarioFilters] = useState(EMPTY_SCENARIO_FILTERS);
  const [conversationFilters, setConversationFilters] = useState(EMPTY_CONVERSATION_FILTERS);

  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ACTIVITY_QUERY_KEYS.overview,
    queryFn: () => api.getActivityOverview(),
  });

  const setTab = useCallback(
    (tab: ActivityTab) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("tab", tab);
      navigate(`/activity?${params.toString()}`, { scroll: false });
    },
    [navigate, searchParams],
  );

  const syncScenarioFilters = useCallback(
    (filters: typeof EMPTY_SCENARIO_FILTERS) => {
      setScenarioFilters(filters);
      const params = scenarioFiltersToSearch(filters);
      params.set("tab", "scenarios");
      navigate(`/activity?${params.toString()}`, { scroll: false });
    },
    [navigate],
  );

  const showDesktopSidebar = hasLearningSidebarContent(overview);

  return (
    <div className="space-y-6">
      <PageHeader
        badge="学习记录"
        title="学习记录"
        description="回顾历史场景与对话，或 AI 生成新的阅读与练习材料"
        action={
          <div className="flex flex-wrap gap-2">
            <Link href="/generate">
              <Button variant="outline">
                <Sparkles className="mr-2 h-4 w-4" />
                生成场景
              </Button>
            </Link>
            <Link href="/chat/new">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                开始新对话
              </Button>
            </Link>
          </div>
        }
      />

      {overviewLoading ? (
        <Spinner label="加载统计..." />
      ) : (
        <LearningStatsBar overview={overview} />
      )}

      <ContinueLearningSection overview={overview} />

      <LearningSidebar overview={overview} mobile />

      <Tabs tabs={TAB_OPTIONS} active={activeTab} onChange={(id) => setTab(id as ActivityTab)} />

      <div
        className={cn(
          showDesktopSidebar && "lg:grid lg:grid-cols-[280px_minmax(0,1fr)] lg:items-start lg:gap-6",
        )}
      >
        {showDesktopSidebar && <LearningSidebar overview={overview} />}
        <div className="min-w-0">
          {activeTab === "scenarios" && (
            <ScenariosTabContent filters={scenarioFilters} onFiltersChange={syncScenarioFilters} />
          )}
          {activeTab === "conversations" && (
            <ConversationsTabContent filters={conversationFilters} onFiltersChange={setConversationFilters} />
          )}
          {activeTab === "timeline" && <TimelineTabContent />}
        </div>
      </div>
    </div>
  );
}

export default function ActivityPage() {
  return (
    <RequireAuth>
      <ActivityHubContent />
    </RequireAuth>
  );
}
