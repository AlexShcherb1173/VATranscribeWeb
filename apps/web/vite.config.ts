import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  const apiTarget = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
  const webBasePath = env.VITE_BASE_PATH || "/";

  return {
    base: webBasePath,
    plugins: [react()],

    resolve: {
      alias: {
        "@": "/src",
      },
    },

    server: {
      host: "0.0.0.0",
      port: 5175,
      strictPort: true,
      open: true,
      proxy: {
        "/api": {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },

    preview: {
      host: "0.0.0.0",
      port: 4175,
      strictPort: true,
    },

    build: {
      target: "es2020",
      outDir: "dist",
      assetsDir: "assets",
      sourcemap: false,
      minify: "esbuild",
      cssCodeSplit: true,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks: {
            react: ["react", "react-dom", "react-router-dom"],
            query: ["@tanstack/react-query"],
            vendor: ["axios"]
          }
        }
      }
    },

    esbuild: {
      drop: mode === "production" ? ["console", "debugger"] : []
    }
  };
});