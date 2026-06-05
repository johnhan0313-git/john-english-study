/** 从 frontend/.env 读取（Next.js 自动加载） */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
