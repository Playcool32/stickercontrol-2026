import { useEffect, useState } from "react";

import { searchStickers, updateNotes } from "../api/client.js";
import { STICKER_ACTIONS } from "../api/stickerActions.js";
import StickerCard from "../components/StickerCard.jsx";
import { IconSearch } from "../components/icons.jsx";

const MIN_QUERY_LENGTH = 2;
const RESULT_LIMIT = 10;

export default function Search() {
  const [query, setQuery] = useState("");
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const q = query.trim();
    if (q.length < MIN_QUERY_LENGTH) {
      setItems([]);
      setTotal(0);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const timer = setTimeout(async () => {
      try {
        const data = await searchStickers({ q, limit: RESULT_LIMIT });
        if (cancelled) return;
        setItems(data.items);
        setTotal(data.total);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }, 300);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [query]);

  const handleAction = async (id, action) => {
    try {
      const updated = await STICKER_ACTIONS[action](id);
      setItems((prev) => prev.map((s) => (s.id === id ? updated : s)));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSaveNotes = async (id, notes) => {
    try {
      const updated = await updateNotes(id, notes);
      setItems((prev) => prev.map((s) => (s.id === id ? updated : s)));
    } catch (err) {
      setError(err.message);
    }
  };

  const showGuide = query.trim().length < MIN_QUERY_LENGTH;

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-2xl font-bold text-gray-800">Buscar figuritas</h2>

      <div className="relative">
        <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-gray-400">
          <IconSearch className="h-5 w-5" />
        </span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Código, país, jugador o número..."
          className="w-full rounded-full border border-gray-200 bg-white py-3 pl-10 pr-4 text-base shadow-sm focus:border-green-500 focus:outline-none"
          autoFocus
        />
      </div>

      {showGuide && (
        <p className="text-sm text-gray-500">
          Buscá por código, país o número. Ej: ARG10, MEX3, FWC1, 00
        </p>
      )}

      {error && <p className="text-faltante">Error: {error}</p>}
      {loading && <p className="text-gray-500">Buscando...</p>}

      {!showGuide && !loading && !error && (
        <p className="text-sm text-gray-500">
          {total > RESULT_LIMIT
            ? `Mostrando ${items.length} de ${total} resultado(s)`
            : `${total} resultado(s)`}
        </p>
      )}

      <div className="flex flex-col gap-3">
        {items.map((sticker) => (
          <StickerCard
            key={sticker.id}
            sticker={sticker}
            onAction={handleAction}
            onSaveNotes={handleSaveNotes}
          />
        ))}
      </div>
    </div>
  );
}
