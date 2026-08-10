/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background) / <alpha-value>)",
        surface: "hsl(var(--surface) / <alpha-value>)",
        "surface-hover": "hsl(var(--surface-hover) / <alpha-value>)",
        border: "hsl(var(--border) / <alpha-value>)",
        foreground: "hsl(var(--foreground) / <alpha-value>)",
        muted: "hsl(var(--muted) / <alpha-value>)",
        "muted-foreground": "hsl(var(--muted-foreground) / <alpha-value>)",
        primary: "hsl(var(--primary) / <alpha-value>)",
        "primary-foreground": "hsl(var(--primary-foreground) / <alpha-value>)",
        destructive: "hsl(var(--destructive) / <alpha-value>)",
        ring: "hsl(var(--ring) / <alpha-value>)",
        card: "hsl(var(--surface) / <alpha-value>)",
        // Pipeline stage semantics — intensity encodes progress, not decoration.
        stage: {
          idle: "hsl(var(--stage-idle) / <alpha-value>)",
          active: "hsl(var(--stage-active) / <alpha-value>)",
          "active-deep": "hsl(var(--stage-active-deep) / <alpha-value>)",
          success: "hsl(var(--stage-success) / <alpha-value>)",
          danger: "hsl(var(--stage-danger) / <alpha-value>)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "sans-serif"],
        sans: ["var(--font-sans)", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
      },
      borderRadius: {
        lg: "10px",
        md: "8px",
        sm: "6px",
      },
      boxShadow: {
        elevated: "0 4px 24px -4px rgb(0 0 0 / 0.4)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
