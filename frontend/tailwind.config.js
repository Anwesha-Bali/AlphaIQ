/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        // Editorial display serif + refined sans + monospace
        display: ['"Fraunces"', "Georgia", "serif"],
        sans: ['"Inter Tight"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        // Hedge-fund terminal palette: deep charcoal, ivory, single sharp accent
        ink: {
          950: "#0a0a0b",
          900: "#101013",
          850: "#16161a",
          800: "#1d1d22",
          700: "#2a2a31",
          600: "#3a3a43",
        },
        bone: {
          50: "#fbfaf6",
          100: "#f4f1e8",
          200: "#e7e2d3",
          300: "#c8c1ad",
          400: "#9a9587",
        },
        // The one accent — a sharp signal-green for grounded answers/citations.
        signal: {
          400: "#a8ff60",
          500: "#7fe34a",
          600: "#5cc12d",
        },
        // Risk severity colors
        risk: {
          low: "#7fe34a",
          medium: "#f5b042",
          high: "#ff5b5b",
        },
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease-out",
        "slide-up": "slideUp 0.45s cubic-bezier(0.2, 0.8, 0.2, 1)",
        "pulse-dot": "pulseDot 1.4s ease-in-out infinite",
        shimmer: "shimmer 2s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
        slideUp: {
          "0%": { opacity: 0, transform: "translateY(8px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
        pulseDot: {
          "0%, 100%": { opacity: 0.3 },
          "50%": { opacity: 1 },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      backgroundImage: {
        "grain":
          "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
