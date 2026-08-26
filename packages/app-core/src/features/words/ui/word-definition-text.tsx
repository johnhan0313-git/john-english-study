import { parseDefinitionByPos } from "../model";

export function WordDefinitionText({ definition }: { definition: string | undefined }) {
  if (!definition?.trim()) {
    return <span className="text-slate-400">暂无中文释义</span>;
  }

  const lines = parseDefinitionByPos(definition);
  if (lines.length === 1 && !lines[0].pos) {
    return <span>{lines[0].text}</span>;
  }

  return (
    <span className="flex flex-col gap-0.5">
      {lines.map((line) => (
        <span key={`${line.pos}-${line.text}`} className="block leading-snug">
          <span className="text-slate-500">{line.pos}</span> {line.text}
        </span>
      ))}
    </span>
  );
}
