import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    // manualChunks for other large deps, Monaco handled by plugin
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined;
          }
          if (
            id.includes("y-monaco") ||
            id.includes("y-websocket") ||
            id.includes("yjs")
          ) {
            return "editor-collab";
          }
          if (id.includes("@xyflow/react")) {
            return "pipeline-graph";
          }
          if (id.includes("xterm") || id.includes("@xterm/")) {
            return "terminal";
          }
          if (id.includes("socket.io-client")) {
            return "realtime";
          }
          if (id.includes("react") || id.includes("react-dom") || id.includes("scheduler")) {
            return "react-vendor";
          }
          return "vendor";
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/socket.io": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
