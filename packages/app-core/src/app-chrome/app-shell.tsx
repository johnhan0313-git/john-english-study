"use client";

import type { ReactNode } from "react";

import { MobileBottomNav } from "./mobile-bottom-nav";
import { Navbar } from "./navbar";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 pb-[calc(5.5rem+env(safe-area-inset-bottom))] pt-6 sm:px-6 md:pb-16">
        {children}
      </main>
      <MobileBottomNav />
    </>
  );
}
