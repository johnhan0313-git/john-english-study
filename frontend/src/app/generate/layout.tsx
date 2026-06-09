import { RequireAuth } from "@/components/auth/require-auth";

export default function GenerateLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
