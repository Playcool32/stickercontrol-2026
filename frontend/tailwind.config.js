/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        faltante: "#ef4444",
        disponible: "#3b82f6",
        pegada: "#22c55e",
        repetida: "#eab308",
      },
    },
  },
  plugins: [],
};
