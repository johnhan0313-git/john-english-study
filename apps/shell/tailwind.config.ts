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
          50: "#eef8f5",
          100: "#d8eee8",
          200: "#adddd1",
          300: "#78c5b4",
          400: "#43aa94",
          500: "#278d79",
          600: "#1d7163",
          700: "#195b51",
          800: "#174940",
          900: "#143d37",
        },
        accent: {
          400: "#f2b768",
          500: "#df9942",
          600: "#bd7830",
        },
        surface: {
          DEFAULT: "#ffffff",
          muted: "#f4f6f5",
          border: "#e2e7e5",
          cream: "#fbfcfb",
          elevated: "#f8faf9",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,35,31,.04), 0 8px 24px rgba(20,35,31,.045)",
        "card-hover": "0 2px 4px rgba(20,35,31,.05), 0 14px 36px rgba(20,35,31,.09)",
        glow: "0 10px 32px rgba(39,141,121,.2)",
        "btn-brand": "0 1px 0 rgba(255,255,255,.18) inset, 0 5px 14px rgba(29,113,99,.2)",
      },
      backgroundImage: {
        "surface-gradient": "linear-gradient(180deg, #fbfcfb 0%, #f6f8f7 100%)",
        "mesh-gradient": "linear-gradient(180deg, rgba(255,255,255,.7), transparent 22rem)",
        "hero-gradient": "linear-gradient(135deg, #278d79 0%, #195b51 100%)",
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
