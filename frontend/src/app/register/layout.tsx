import { Suspense } from "react";
import { Spinner } from "@/components/ui";

export default function RegisterLayout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<Spinner label="加载..." />}>{children}</Suspense>;
}
