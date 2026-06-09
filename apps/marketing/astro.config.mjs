import { defineConfig } from "astro/config";

export default defineConfig({
  site: "https://vatranscribe.example.com",
  output: "static",
  server: {
    host: "0.0.0.0",
    port: 4321
  },
  build: {
    format: "directory"
  }
});
