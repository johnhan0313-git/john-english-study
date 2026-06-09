"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

export default function RegisterRedirectPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const next = searchParams.get("next");
    const query = next ? `?next=${encodeURIComponent(next)}` : "";
    router.replace(`/login${query}`);
  }, [router, searchParams]);

  return null;
}
