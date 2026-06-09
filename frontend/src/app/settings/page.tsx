"use client";

import { useQuery } from "@tanstack/react-query";
import { API_BASE } from "@/lib/env";
import { Alert, Button, Card, PageHeader } from "@/components/ui";
import { useAuth } from "@/contexts/auth-context";

type AIEndpointStatus = {
  base_url: string;
  model: string;
  has_api_key: boolean;
  configured: boolean;
};

type AIConfig = {
  llm: AIEndpointStatus;
  stt: AIEndpointStatus;
  tts: AIEndpointStatus;
  use_edge_tts: boolean;
  using_mock: boolean;
};

function EndpointRow({
  label,
  endpoint,
}: {
  label: string;
  endpoint: AIEndpointStatus;
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-3">
      <h3 className="text-sm font-medium text-slate-700">{label}</h3>
      <dl className="mt-2 space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Base URL</dt>
          <dd className="font-mono text-right break-all">{endpoint.base_url}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Model</dt>
          <dd className="font-mono">{endpoint.model}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">API Key</dt>
          <dd>{endpoint.has_api_key ? "已配置" : "未配置"}</dd>
        </div>
      </dl>
    </div>
  );
}

export default function SettingsPage() {
  const { user, isAuthenticated, logout } = useAuth();
  const { data } = useQuery<AIConfig>({
    queryKey: ["ai-config"],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/config/ai`);
      return res.json();
    },
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader badge="系统" title="设置" description="账号、前后端环境变量与 AI 服务配置" />

      <Card>
        <h2 className="font-semibold">账号</h2>
        {isAuthenticated && user ? (
          <dl className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-slate-500">用户名</dt>
              <dd>{user.username}</dd>
            </div>
            {user.email && (
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">邮箱</dt>
                <dd>{user.email}</dd>
              </div>
            )}
            <div className="pt-2">
              <Button variant="outline" size="sm" onClick={logout}>
                退出登录
              </Button>
            </div>
          </dl>
        ) : (
          <p className="mt-2 text-sm text-slate-600">
            未登录。学习进度与场景数据需登录后保存。
          </p>
        )}
      </Card>

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
          LLM、STT、TTS 可分别配置不同的 API 来源。在 backend/.env 中设置 AI_LLM_*、AI_STT_*、AI_TTS_*。
          LLM 未配置走 Mock；STT 未配置口语评测报错；TTS 默认使用 Edge TTS。
        </p>
        {data && (
          <>
            {data.using_mock && (
              <Alert variant="warning">
                LLM 未配置，场景生成使用 Mock 固定内容。请配置 AI_LLM_API_KEY 并重启后端。
              </Alert>
            )}
            <div className="mt-4 space-y-3">
              <EndpointRow label="LLM（场景 / 写作批改）" endpoint={data.llm} />
              <EndpointRow label="STT（口语识别）" endpoint={data.stt} />
              {data.use_edge_tts ? (
                <div className="rounded-lg border border-slate-200 p-3">
                  <h3 className="text-sm font-medium text-slate-700">TTS（听力朗读）</h3>
                  <p className="mt-2 text-sm text-slate-600">Edge TTS（免费）</p>
                </div>
              ) : (
                <EndpointRow label="TTS（听力朗读）" endpoint={data.tts} />
              )}
            </div>
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
