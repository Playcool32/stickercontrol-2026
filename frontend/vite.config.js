import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// En producción (SkillGames) la app se sirve bajo /stickercontrol/, por eso
// el build usa esa base. En desarrollo se usa "/" y el proxy de Vite hacia
// el backend en :8000. VITE_BASE la reemplaza (la demo se sirve en la raíz
// de stickercontrol-demo.roura.com.ar, con VITE_BASE=/).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  return {
    base: env.VITE_BASE || (mode === "production" ? "/stickercontrol/" : "/"),
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
  };
});
