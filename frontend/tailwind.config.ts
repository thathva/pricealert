import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'JetBrains Mono'", "ui-monospace", "monospace"],
      },
      colors: {
        surface: {
          base: "#0d1117",
          card: "#161b22",
          hover: "#1c2128",
        },
        border: "#30363d",
        ink: {
          DEFAULT: "#c9d1d9",
          muted: "#8b949e",
          dim: "#484f58",
        },
        state: {
          queued:      "#8b949e",
          sending:     "#58a6ff",
          delivered:   "#3fb950",
          failed:      "#f85149",
          dead_letter: "#bc8cff",
        },
      },
    },
  },
  plugins: [],
};

export default config;
