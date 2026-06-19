import type { Metadata, Viewport } from "next";
import { Inter, Plus_Jakarta_Sans } from "next/font/google";

import "@sceneenglish/app-core/styles/globals.css";
import { WebRootLayout } from "@/platform/web-root-layout";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SceneEnglish - CET-4/6 场景英语学习",
  description: "成人英语场景学习平台，兼顾听说读写",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className={`${inter.variable} ${jakarta.variable} font-sans app-shell`}>
        <WebRootLayout>{children}</WebRootLayout>
      </body>
    </html>
  );
}
