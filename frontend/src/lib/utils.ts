import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const DEVICE_ID_KEY = "john-english-device-id";

export function getDeviceId(): string {
  if (typeof window === "undefined") return "default";
  let id = localStorage.getItem(DEVICE_ID_KEY);
  if (!id) {
    id = `device_${Math.random().toString(36).slice(2, 10)}`;
    localStorage.setItem(DEVICE_ID_KEY, id);
  }
  return id;
}
