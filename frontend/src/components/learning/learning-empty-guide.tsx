import Link from "next/link";
import { MessageCircle, Sparkles } from "lucide-react";
import { Button, Card } from "@/components/ui";

interface LearningEmptyGuideProps {
  variant: "scenarios" | "conversations";
}

const EXAMPLES = {
  scenarios: {
    title: "The Cloud Revolution",
    meta: "technology · 10 词 · CET4",
    description: "AI 会根据你的词库生成沉浸式阅读场景",
  },
  conversations: {
    title: "Coffee Shop Chat",
    meta: "日常对话 · 8 轮 · CET4",
    description: "与 AI 角色扮演，在真实语境中练习口语表达",
  },
};

export function LearningEmptyGuide({ variant }: LearningEmptyGuideProps) {
  const example = EXAMPLES[variant];

  return (
    <div className="space-y-6">
      <Card className="border-dashed opacity-75">
        <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">示例预览</p>
        <h3 className="font-bold text-slate-700">{example.title}</h3>
        <p className="mt-1 text-sm text-slate-500">{example.meta}</p>
        <p className="mt-2 text-sm text-slate-400">{example.description}</p>
      </Card>
      <div className="flex flex-wrap justify-center gap-3">
        {variant === "scenarios" ? (
          <Link href="/generate">
            <Button>
              <Sparkles className="mr-2 h-4 w-4" />
              生成场景
            </Button>
          </Link>
        ) : (
          <Link href="/chat/new">
            <Button>
              <MessageCircle className="mr-2 h-4 w-4" />
              开始新对话
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
}
