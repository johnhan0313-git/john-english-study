import type { ConversationDetail } from "@sceneenglish/api-client/types";

const KNOWN_THEMES = new Set([
  "travel",
  "campus",
  "business",
  "health",
  "technology",
  "environment",
  "culture",
  "daily",
]);

export interface ConversationVisuals {
  themeKey: string;
  backgroundUrl: string;
  portraitUrl: string;
  ambientLabel: string;
  roleLabel: string;
}

export function slugifyRole(role: string): string {
  return role
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 32) || "assistant";
}

function normalizeTheme(theme: string | undefined): string {
  const key = (theme || "daily").toLowerCase().trim();
  return KNOWN_THEMES.has(key) ? key : "default";
}

export function resolveConversationVisuals(session: Pick<
  ConversationDetail,
  "theme" | "role_ai" | "scene_brief" | "title"
>): ConversationVisuals {
  const themeKey = normalizeTheme(session.theme);
  const roleSlug = slugifyRole(session.role_ai);
  const sceneBrief = session.scene_brief ?? {};

  return {
    themeKey,
    backgroundUrl: `/scenes/${themeKey}.svg`,
    portraitUrl: `/avatars/${themeKey}.svg`,
    ambientLabel: sceneBrief.location || sceneBrief.task || session.title,
    roleLabel: session.role_ai || roleSlug,
  };
}
