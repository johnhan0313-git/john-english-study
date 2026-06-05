"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { getDeviceId } from "@/lib/utils";
import { Badge, Card, Spinner } from "@/components/ui";

export default function ScenariosPage() {
  const deviceId = getDeviceId();
  const { data, isLoading } = useQuery({
    queryKey: ["scenarios", deviceId],
    queryFn: () => api.listScenarios(deviceId),
  });

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">场景列表</h1>
      {isLoading ? (
        <Spinner />
      ) : (
        <div className="space-y-3">
          {data?.items.map((s) => (
            <Link key={s.id} href={`/scenarios/${s.id}`}>
              <Card className="transition-shadow hover:shadow-md">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{s.title}</h3>
                    <p className="text-sm text-slate-500">
                      {s.theme} · {s.word_count} 词 · {new Date(s.created_at).toLocaleDateString("zh-CN")}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {s.is_daily && <Badge variant="success">每日</Badge>}
                    <Badge>{s.level.toUpperCase()}</Badge>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
          {!data?.items.length && (
            <Card className="text-center text-slate-500">暂无场景，去首页或生成页创建吧</Card>
          )}
        </div>
      )}
    </div>
  );
}
