"use client";

import { useEffect } from "react";

import { useNavigate } from "../platform/context";

export default function ReferenceIndexPage() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/reference/phonetics", { replace: true });
  }, [navigate]);
  return null;
}
