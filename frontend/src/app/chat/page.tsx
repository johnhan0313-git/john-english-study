"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { MessageCircle, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Button, Card, EmptyState, PageHeader, Spinner } from "@/components/ui";

export default function ChatListPage() {
  const deviceId = getDeviceId();

  const { data, isLoading } = useQuery({
    queryKey: ["conversations", deviceId],
    queryFn: () => api.listConversations(deviceId),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        badge="1v1 对话"
        title="场景对话练习"
        description="与 AI 角色扮演，在真实语境中练习 CET-4/6 词汇与口语表达"
        action={
          <Link href="/chat/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              开始新对话
            </Button>
          </Link>
        }
      />

      {isLoading ? (
        <Spinner label="加载对话..." />
      ) : data?.items.length ? (
        <div className="space-y-3">
          {data.items.map((item) => (
            <Link key={item.id} href={`/chat/${item.id}`} className="block">
              <Card hover className="group">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="font-semibold text-slate-900 group-hover:text-brand-700">{item.title}</h3>
                      <Badge variant={item.status === "active" ? "brand" : "default"}>
                        {item.status === "active" ? "进行中" : "已结束"}
                      </Badge>
                      <Badge variant="outline">{item.level.toUpperCase()}</Badge>
                    </div>
                    <p className="mt-1 text-sm text-slate-500">
                      {item.role_ai} · {item.turn_count} 轮 · 已用 {item.words_used.length}/{item.target_words.length} 词
                    </p>
                    {item.last_message && (
                      <p className="mt-2 line-clamp-2 text-sm text-slate-600">{item.last_message}</p>
                    )}
                  </div>
                  <MessageCircle className="h-5 w-5 shrink-0 text-brand-400" />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState
          title="还没有对话记录"
          description="创建一个新对话，开始 1v1 场景角色扮演练习"
          action={
            <Link href="/chat/new">
              <Button>开始新对话</Button>
            </Link>
          }
        />
      )}
    </div>
  );
}
