import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans:  ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono:  ["var(--font-geist-mono)", "ui-monospace", "monospace"],
        serif: ["var(--font-spectral)", "Georgia", "serif"],
      },
      boxShadow: {
        hard:    "2px 2px 0 oklch(0% 0 0)",
        "hard-sm": "1px 1px 0 oklch(0% 0 0)",
      },
    },
  },
  plugins: [],
};
export default config;
