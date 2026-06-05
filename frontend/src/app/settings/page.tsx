"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card } from "@/components/ui";

export default function SettingsPage() {
  const { data } = useQuery({
    queryKey: ["ai-config"],
    queryFn: async () => {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/config/ai`);
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
        <h2 className="font-semibold">AI 配置</h2>
        <p className="mt-2 text-sm text-slate-600">
          AI 相关配置通过后端环境变量设置。复制 <code className="rounded bg-slate-100 px-1">.env.example</code> 为{" "}
          <code className="rounded bg-slate-100 px-1">.env</code> 并填入你的 OpenAI 兼容 API Key。
        </p>
        {data && (
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
