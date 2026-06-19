import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  base: "/ui/", // assets served under Flask's /ui/ route
  plugins: [react()],
  resolve: {
    alias: { "askdiana-ui": path.resolve(__dirname, "../../ui/src/index.ts") },
    dedupe: ["react", "react-dom"], // single React across the aliased source + app
  },
  build: { outDir: "static", emptyOutDir: true },
});
