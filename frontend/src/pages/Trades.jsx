import { useEffect, useState } from "react";

import { getNearby, getTradeMatch } from "../api/client.js";
import TradeResultPanel from "../components/TradeResultPanel.jsx";

export default function Trades() {
  const [nearby, setNearby] = useState(null);
  const [error, setError] = useState(null);
  const [trades, setTrades] = useState({});
  const [tradeErrors, setTradeErrors] = useState({});

  useEffect(() => {
    getNearby()
      .then(setNearby)
      .catch((err) => setError(err.message));
  }, []);

  const handleCalculateTrade = async (userId) => {
    setTradeErrors((e) => ({ ...e, [userId]: null }));
    try {
      const trade = await getTradeMatch(userId);
      setTrades((t) => ({ ...t, [userId]: trade }));
    } catch (err) {
      setTradeErrors((e) => ({ ...e, [userId]: err.message }));
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Intercambios</h2>
        <p className="text-sm text-gray-600">
          Calculá qué podés dar y qué te puede dar cada coleccionista público cercano, cruzando
          tus repetidas y faltantes con las suyas.
        </p>
      </div>

      {error && <p className="text-faltante">Error: {error}</p>}
      {!error && !nearby && <p className="text-gray-500">Cargando...</p>}

      {nearby && nearby.users.length === 0 && (
        <p className="text-gray-600">
          Todavía no hay otros usuarios públicos cerca. Activá tu perfil público en "Usuarios
          cerca" y volvé más tarde.
        </p>
      )}

      <div className="flex flex-col gap-4">
        {nearby?.users.map((user) => (
          <div key={user.user_id} className="rounded-2xl bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="text-lg font-bold text-gray-800">{user.display_name}</p>
                <p className="text-sm text-gray-500">{user.city || "Ciudad no especificada"}</p>
              </div>
              <button
                type="button"
                onClick={() => handleCalculateTrade(user.user_id)}
                className="flex-shrink-0 rounded-xl bg-green-600 px-3 py-2 text-sm font-bold text-white"
              >
                Calcular intercambio
              </button>
            </div>

            {tradeErrors[user.user_id] && (
              <p className="mt-2 text-sm text-faltante">Error: {tradeErrors[user.user_id]}</p>
            )}
            {trades[user.user_id] && <TradeResultPanel trade={trades[user.user_id]} />}
          </div>
        ))}
      </div>
    </div>
  );
}
