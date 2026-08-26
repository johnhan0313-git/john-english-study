export const ACCESS_TOKEN_KEY = "john-english-access-token";
export const DEVICE_ID_KEY = "john-english-device-id";

let cachedAccessToken: string | null = null;

export function getAccessTokenSync(): string | null {
  return cachedAccessToken;
}

export function setAccessTokenCache(token: string | null): void {
  cachedAccessToken = token;
}

export async function loadAccessToken(
  get: (key: string) => Promise<string | null>,
): Promise<string | null> {
  cachedAccessToken = await get(ACCESS_TOKEN_KEY);
  return cachedAccessToken;
}

export async function persistAccessToken(
  storage: { set: (k: string, v: string) => Promise<void>; remove: (k: string) => Promise<void> },
  token: string | null,
): Promise<void> {
  cachedAccessToken = token;
  if (token) {
    await storage.set(ACCESS_TOKEN_KEY, token);
  } else {
    await storage.remove(ACCESS_TOKEN_KEY);
  }
}
