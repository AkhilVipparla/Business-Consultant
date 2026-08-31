import type { Config } from "tailwindcss";

// Warm Retro Editorial palette — see anchor.md/UI_UX_GUIDELINES.md
const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: "#F5EFEB",
        surface: "#FAF7F3",
        charcoal: "#2B2B2B",
        terracotta: "#C84B31",
        tan: "#EAE3D2",
        olive: "#4A6B41",
        border: "#DCD3C4",
        muted: "#6B6459",
        warning: "#B8863B",
        error: "#B23A2E",
        info: "#3B6B8C",
      },
      fontFamily: {
        heading: ["var(--font-fraunces)"],
        sans: ["var(--font-inter)"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
    },
  },
  plugins: [],
};

export default config;
