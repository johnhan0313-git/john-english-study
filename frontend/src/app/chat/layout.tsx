import { RequireAuth } from "@/components/auth/require-auth";

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return <RequireAuth>{children}</RequireAuth>;
}
