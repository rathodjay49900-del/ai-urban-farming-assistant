/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#16A34A",
        secondary: "#22C55E",
        dark: "#14532D",
        ai: "#6366F1",
        sky: "#0EA5E9",
        warning: "#F59E0B",
        danger: "#EF4444",
        success: "#10B981",
        background: "var(--app-background)",
        card: "var(--app-card)",
        text: "var(--app-text)",
        muted: "var(--app-muted)",
        border: "var(--app-border)"
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        heading: ['Poppins', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
