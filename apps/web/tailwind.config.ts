import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
    "../../packages/app-core/src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
        },
        accent: {
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
        },
        surface: {
          DEFAULT: "#ffffff",
          muted: "#fdfaf6",
          border: "#e8e2da",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "system-ui"],
      },
      boxShadow: {
        card: "0 1px 3px rgba(28,25,23,.06), 0 8px 24px rgba(234,88,12,.06)",
        "card-hover": "0 4px 12px rgba(28,25,23,.08), 0 16px 40px rgba(234,88,12,.1)",
        glow: "0 0 40px rgba(249,115,22,.14)",
      },
      backgroundImage: {
        "mesh-gradient":
          "radial-gradient(at 40% 20%, rgba(249,115,22,.09) 0, transparent 50%), radial-gradient(at 80% 0%, rgba(245,158,11,.07) 0, transparent 50%), radial-gradient(at 0% 50%, rgba(251,146,60,.05) 0, transparent 50%)",
        "hero-gradient": "linear-gradient(135deg, #ea580c 0%, #f97316 55%, #f59e0b 100%)",
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
};

export default config;
