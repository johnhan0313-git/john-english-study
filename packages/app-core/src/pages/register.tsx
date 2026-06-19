"use client";

import { useNavigate, useSearchParams } from "@sceneenglish/app-core/platform/context";
import { useEffect } from "react";

export default function RegisterRedirectPage() {
  const navigate = useNavigate();
  const searchParams = useSearchParams();

  useEffect(() => {
    const next = searchParams.get("next");
    const query = next ? `?next=${encodeURIComponent(next)}` : "";
    navigate(`/login${query}`);
  }, [navigate, searchParams]);

  return null;
}
