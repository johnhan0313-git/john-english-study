import { Suspense } from "react";
import { Spinner } from "@/components/ui";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Spinner label="加载..." />}>{children}</Suspense>;
}
