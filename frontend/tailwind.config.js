/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111827",
        "surface-raised": "#1e293b",
        border: "#1f293d",
        good: {
          DEFAULT: "#10b981",
          light: "#d1fae5",
          dark: "#065f46"
        },
        moderate: {
          DEFAULT: "#f59e0b",
          light: "#fef3c7",
          dark: "#78350f"
        },
        poor: {
          DEFAULT: "#ef4444",
          light: "#fee2e2",
          dark: "#7f1d1d"
        }
      }
    },
  },
  plugins: [],
}
