import { IconSwap } from "../components/icons.jsx";

export default function Trades() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-2xl bg-white p-8 text-center shadow-sm">
      <span className="flex h-14 w-14 items-center justify-center rounded-full bg-green-100 text-green-600">
        <IconSwap className="h-7 w-7" />
      </span>
      <h2 className="text-2xl font-bold text-gray-800">Intercambios</h2>
      <p className="text-gray-600">
        Próximamente: vas a poder calcular intercambios cruzando tus repetidas y faltantes
        con las de otro coleccionista, y generar el resumen para WhatsApp.
      </p>
    </div>
  );
}
