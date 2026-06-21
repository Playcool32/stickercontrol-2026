import { useState } from "react";

import { IconCheck, IconCopy } from "./icons.jsx";

// Resultado de "Calcular intercambio" (Fase 2D), reutilizado por Nearby.jsx
// y Trades.jsx para no duplicar el render de la tarjeta dar/recibir.
export default function TradeResultPanel({ trade }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(trade.summary_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-3 flex flex-col gap-2 rounded-xl bg-gray-50 p-3">
      <div className="flex flex-wrap gap-2 text-xs font-semibold">
        <span className="rounded-full bg-yellow-50 px-3 py-1 text-yellow-700">
          Vos podés darle: {trade.i_can_give.length > 0 ? trade.i_can_give.join(", ") : "(ninguna)"}
        </span>
        <span className="rounded-full bg-red-50 px-3 py-1 text-faltante">
          Te puede dar: {trade.i_can_receive.length > 0 ? trade.i_can_receive.join(", ") : "(ninguna)"}
        </span>
      </div>
      <button
        type="button"
        onClick={handleCopy}
        className="flex w-fit items-center gap-1.5 rounded-xl bg-gray-200 px-3 py-2 text-sm font-bold text-gray-700"
      >
        {copied ? <IconCheck className="h-4 w-4" /> : <IconCopy className="h-4 w-4" />}
        {copied ? "¡Copiado!" : "Copiar resumen para WhatsApp"}
      </button>
    </div>
  );
}
