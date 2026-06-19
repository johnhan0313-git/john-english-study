/** 从 frontend/.env 或 Docker build-arg 读取；生产可设为相对路径 `/api` 与页面同域同协议 */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
