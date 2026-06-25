import type { Config } from "tailwindcss";

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "../../packages/app-core/src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff8f4",
          100: "#ffefe6",
          200: "#ffe0d1",
          300: "#ffc9b3",
          400: "#ffad8a",
          500: "#ff9268",
          600: "#f07850",
          700: "#e06545",
          800: "#c45238",
          900: "#a34430",
        },
        accent: {
          400: "#ffd280",
          500: "#ffc266",
          600: "#f0a840",
        },
        surface: {
          DEFAULT: "#ffffff",
          muted: "#fff9f5",
          border: "#f2e8df",
          cream: "#fffcfa",
          elevated: "#fffbf8",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(68,45,35,.04), 0 4px 16px rgba(255,146,104,.07), 0 12px 32px rgba(68,45,35,.04)",
        "card-hover": "0 2px 8px rgba(68,45,35,.06), 0 8px 24px rgba(255,146,104,.12), 0 20px 48px rgba(68,45,35,.06)",
        glow: "0 0 32px rgba(255,173,138,.35), 0 8px 24px rgba(240,120,80,.18)",
        "btn-brand": "0 1px 0 rgba(255,255,255,.28) inset, 0 4px 14px rgba(240,120,80,.28), 0 1px 3px rgba(68,45,35,.08)",
      },
      backgroundImage: {
        "surface-gradient": "linear-gradient(180deg, #fffcfa 0%, #fff7f2 42%, #fff1e9 100%)",
        "mesh-gradient":
          "radial-gradient(ellipse 80% 50% at 15% -10%, rgba(255,201,179,.45) 0, transparent 55%), radial-gradient(ellipse 60% 45% at 95% 5%, rgba(255,210,128,.28) 0, transparent 50%), radial-gradient(ellipse 50% 40% at 50% 100%, rgba(255,173,138,.18) 0, transparent 55%)",
        "hero-gradient": "linear-gradient(165deg, #ffc9ad 0%, #ff9a70 42%, #f07850 78%, #ffc266 100%)",
      },
      animation: {
        "fade-in": "fadeIn .4s ease-out",
        "slide-up": "slideUp .45s ease-out",
        shimmer: "shimmer 2s infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        shimmer: { "0%,100%": { opacity: "1" }, "50%": { opacity: ".6" } },
      },
    },
  },
  plugins: [],
} satisfies Config;
