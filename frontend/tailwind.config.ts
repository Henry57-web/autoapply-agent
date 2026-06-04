import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        mist: "#eef3f5",
        leaf: "#2f6f5e",
        coral: "#c45c4a",
      },
    },
  },
  plugins: [],
};

export default config;
