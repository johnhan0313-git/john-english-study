import type { PlatformAudio, PlatformRecorder, PlatformStorage } from "./types";

export function createLocalStorageAdapter(): PlatformStorage {
  return {
    async get(key) {
      if (typeof localStorage === "undefined") return null;
      return localStorage.getItem(key);
    },
    async set(key, value) {
      localStorage.setItem(key, value);
    },
    async remove(key) {
      localStorage.removeItem(key);
    },
  };
}

export function createMediaRecorderAdapter(): PlatformRecorder {
  let recorder: MediaRecorder | null = null;
  let stream: MediaStream | null = null;
  const chunks: Blob[] = [];

  return {
    async start() {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recorder = new MediaRecorder(stream);
      chunks.length = 0;
      recorder.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      recorder.start();
    },
    async stop() {
      if (!recorder) throw new Error("Recorder not started");
      return new Promise<Blob>((resolve, reject) => {
        recorder!.onstop = () => {
          stream?.getTracks().forEach((t) => t.stop());
          stream = null;
          recorder = null;
          resolve(new Blob(chunks, { type: "audio/webm" }));
        };
        recorder!.onerror = () => reject(new Error("Recording failed"));
        recorder!.stop();
      });
    },
  };
}

export function createHtmlAudioAdapter(): PlatformAudio {
  let audio: HTMLAudioElement | null = null;
  return {
    async play(url) {
      if (audio) {
        audio.pause();
      }
      audio = new Audio(url);
      await audio.play();
    },
    setRate(rate) {
      if (audio) audio.playbackRate = rate;
    },
    pause() {
      audio?.pause();
    },
  };
}

export const DEVICE_ID_KEY = "john-english-device-id";

export async function getOrCreateBrowserDeviceId(storage: PlatformStorage): Promise<string> {
  let id = await storage.get(DEVICE_ID_KEY);
  if (!id) {
    id = `device_${Math.random().toString(36).slice(2, 10)}`;
    await storage.set(DEVICE_ID_KEY, id);
  }
  return id;
}

export function createBasePlatform(
  navigation: import("./types").PlatformNavigation,
  opts: {
    apiBase: string;
    runtime: import("./types").RuntimePlatform;
    storage?: PlatformStorage;
    onUnauthorized?: () => void;
  },
): import("./types").PlatformServices {
  const storage = opts.storage ?? createLocalStorageAdapter();
  return {
    navigation,
    storage,
    getDeviceId: () => getOrCreateBrowserDeviceId(storage),
    getApiBase: () => opts.apiBase,
    getRuntime: () => opts.runtime,
    openExternal(url) {
      window.open(url, "_blank", "noopener,noreferrer");
    },
    recorder: createMediaRecorderAdapter(),
    audio: createHtmlAudioAdapter(),
    onUnauthorized: opts.onUnauthorized,
  };
}
