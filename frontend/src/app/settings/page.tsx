"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE } from "@/lib/env";
import { Card } from "@/components/ui";

export default function SettingsPage() {
  const { data } = useQuery({
    queryKey: ["ai-config"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/config/ai`);
      return res.json();
    },
  });

  return (
    <div className="space-y-6 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold">设置</h1>
        <p className="text-slate-600">API 与系统配置</p>
      </div>

      <Card>
        <h2 className="font-semibold">前端配置</h2>
        <p className="mt-2 text-sm text-slate-600">
          前端环境变量写在 frontend/.env。复制 frontend/.env.example 为 frontend/.env，修改后需重启{" "}
          <code className="rounded bg-slate-100 px-1">npm run dev</code>。
        </p>
        <dl className="mt-4 space-y-2 text-sm">
          <div className="flex justify-between">
            <dt className="text-slate-500">API 地址</dt>
            <dd className="font-mono">{API_BASE}</dd>
          </div>
        </dl>
      </Card>

      <Card>
        <h2 className="font-semibold">后端 AI 配置</h2>
        <p className="mt-2 text-sm text-slate-600">
          后端环境变量写在 backend/.env。复制 backend/.env.example 为 backend/.env 并填入 API Key。
        </p>
        {data && (
          <>
            {data.using_mock && (
              <div className="mt-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
                当前使用 Mock 模式，场景固定为「A Day at the Airport」。请在 backend/.env 中配置 AI_API_KEY 并重启后端。
              </div>
            )}
            <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-slate-500">API Base URL</dt>
              <dd className="font-mono">{data.base_url}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">Model</dt>
              <dd className="font-mono">{data.model}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">API Key</dt>
              <dd>{data.has_api_key ? "已配置" : "未配置（使用 Mock）"}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-500">TTS</dt>
              <dd>{data.use_edge_tts ? "Edge TTS（免费）" : "OpenAI TTS"}</dd>
            </div>
            </dl>
          </>
        )}
      </Card>

      <Card>
        <h2 className="font-semibold">本地部署</h2>
        <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900 p-4 text-sm text-slate-100">
{`# 后端
cd backend && pip install -e .
uvicorn app.main:app --reload

# 前端
cd frontend && npm install && npm run dev

# Docker
docker compose up --build`}
        </pre>
      </Card>
    </div>
  );
}
