import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// En producción (SkillGames) la app se sirve bajo /stickercontrol/, por eso
// el build usa esa base. En desarrollo se usa "/" y el proxy de Vite hacia
// el backend en :8000.
export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/stickercontrol/" : "/",
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
}));
