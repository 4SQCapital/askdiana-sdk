import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  return {
    base: env.VITE_BASE_URL ?? "/ui/",
    plugins: [react(), viteSingleFile()],
    build: { outDir: "static", emptyOutDir: true, cssCodeSplit: false },
  };
});
