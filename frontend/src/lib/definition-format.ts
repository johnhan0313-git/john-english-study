/** 词性展示顺序（固定） */
export const POS_DISPLAY_ORDER = [
  "n.",
  "adj.",
  "adv.",
  "v.",
  "vt.",
  "vi.",
  "prep.",
  "conj.",
  "pron.",
  "int.",
  "num.",
  "art.",
] as const;

const POS_MARKER_PATTERN =
  /\b(n\.|adj\.|adv\.|vt\.|vi\.|v\.|prep\.|conj\.|pron\.|int\.|num\.|art\.)\s*/gi;

export interface DefinitionLine {
  pos: string;
  text: string;
}

function posSortIndex(pos: string): number {
  const normalized = pos.toLowerCase();
  const idx = POS_DISPLAY_ORDER.indexOf(normalized as (typeof POS_DISPLAY_ORDER)[number]);
  return idx === -1 ? POS_DISPLAY_ORDER.length : idx;
}

/** 将「adj. … n. … vt. …」合并释义拆成按词性分行的条目，并按固定顺序排序 */
export function parseDefinitionByPos(definition: string): DefinitionLine[] {
  const trimmed = definition.trim();
  if (!trimmed) return [];

  const markers: { pos: string; start: number; contentStart: number }[] = [];
  let match: RegExpExecArray | null;
  const regex = new RegExp(POS_MARKER_PATTERN.source, "gi");

  while ((match = regex.exec(trimmed)) !== null) {
    markers.push({
      pos: match[1].toLowerCase(),
      start: match.index,
      contentStart: match.index + match[0].length,
    });
  }

  if (markers.length === 0) {
    return [{ pos: "", text: trimmed }];
  }

  const lines: DefinitionLine[] = markers.map((marker, index) => {
    const contentEnd = index + 1 < markers.length ? markers[index + 1].start : trimmed.length;
    return {
      pos: marker.pos,
      text: trimmed.slice(marker.contentStart, contentEnd).trim(),
    };
  });

  return lines
    .filter((line) => line.text)
    .sort((a, b) => posSortIndex(a.pos) - posSortIndex(b.pos));
}

/** 列表/表格用的单行释义预览 */
export function definitionPreview(definition: string | undefined, maxLen = 72): string {
  if (!definition?.trim()) return "暂无中文释义";
  const lines = parseDefinitionByPos(definition);
  const text = lines
    .map((line) => (line.pos ? `${line.pos} ${line.text}` : line.text))
    .join(" · ");
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen)}…`;
}
