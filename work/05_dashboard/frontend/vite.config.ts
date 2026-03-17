import { resolve } from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  base: "./",
  define: {
    __REPO_ROOT__: JSON.stringify(resolve(__dirname, "..", "..", "..")),
  },
  server: {
    port: 4173,
    fs: {
      allow: [resolve(__dirname, "..", "..", "..")],
    },
  },
});
