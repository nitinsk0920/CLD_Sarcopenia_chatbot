/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hospital: {
          50: "#f3f8fc",
          100: "#e7f0f8",
          200: "#cddfed",
          300: "#a9c6dd",
          400: "#7fa7c7",
          500: "#638aaf",
          600: "#4f7094",
          700: "#425b78",
          800: "#3a4d64",
          900: "#344357",
        },
        care: {
          50: "#eefbf5",
          100: "#d8f5e7",
          200: "#b7eaca",
          300: "#8dd9a8",
          400: "#60bf82",
          500: "#3fa164",
          600: "#2f8250",
          700: "#296942",
          800: "#245437",
          900: "#1f452f",
        },
      },
      boxShadow: {
        soft: "0 8px 30px rgba(38, 66, 97, 0.08)",
      },
      fontFamily: {
        sans: ["Segoe UI", "Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
