import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// Only API prefixes are proxied. Frontend routes are singular (/card, /set, /color),
// API paths are plural (/cards, /sets), so the two never collide.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/cards": "http://127.0.0.1:8000",
      "/sets": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["src/test/setup.ts"],
  },
});
