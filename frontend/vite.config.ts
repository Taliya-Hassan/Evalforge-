import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, /api/* is proxied to the FastAPI server so there are no CORS problems.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
