import { useEffect, useState } from "react";

import { getDuplicates } from "../api/client.js";
import { IconCheck, IconCopy } from "../components/icons.jsx";

export default function Duplicates() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getDuplicates()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (error) return <p className="text-faltante">Error: {error}</p>;
  if (!data) return <p className="text-gray-500">Cargando...</p>;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-2xl font-bold text-gray-800">Repetidas</h2>

      <button
        type="button"
        onClick={handleCopy}
        className="flex items-center justify-center gap-2 rounded-2xl bg-repetida p-4 text-lg font-bold text-black shadow-sm active:opacity-80"
      >
        {copied ? <IconCheck className="h-5 w-5" /> : <IconCopy className="h-5 w-5" />}
        {copied ? "¡Copiado!" : "Copiar para WhatsApp"}
      </button>

      {data.by_country.length === 0 && (
        <p className="rounded-2xl bg-white p-4 text-center text-gray-600 shadow-sm">
          No tenés figuritas repetidas.
        </p>
      )}

      {data.by_country.map((country) => (
        <div key={country.country_code} className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="font-bold text-gray-800">
            {country.country_name} ({country.country_code})
          </p>
          <div className="mt-2 flex flex-wrap gap-2 md:gap-1">
            {country.items.map((item) => (
              <span
                key={item.number}
                className="flex items-center justify-center rounded-full bg-yellow-50 px-3 py-3 text-sm font-bold text-yellow-700 md:px-2 md:py-1 md:text-xs md:font-semibold"
              >
                {(() => {
                  const label = item.number === 0 ? "00" : item.number;
                  return item.quantity > 1 ? `${label} (x${item.quantity})` : label;
                })()}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
