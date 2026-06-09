import { RequireAuth } from "@/components/auth/require-auth";

export default function ProgressLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
