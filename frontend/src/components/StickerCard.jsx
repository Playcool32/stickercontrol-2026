import { useState } from "react";

import { getCountryLabel } from "../utils/countryLabel.js";
import { getFlagUrl } from "../utils/flags.js";
import { IconAlert, IconCheck, IconMinus, IconPlus } from "./icons.jsx";
import StatusBadge from "./StatusBadge.jsx";

export default function StickerCard({ sticker, onAction, onSaveNotes }) {
  const [notes, setNotes] = useState(sticker.notes || "");
  const [savingNotes, setSavingNotes] = useState(false);
  const [flagError, setFlagError] = useState(false);

  const handleSaveNotes = async () => {
    setSavingNotes(true);
    try {
      await onSaveNotes(sticker.id, notes);
    } finally {
      setSavingNotes(false);
    }
  };

  const flagUrl = getFlagUrl(sticker.country_code);

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-sm">
      <div className="flex items-start gap-3">
        {flagUrl && !flagError && (
          <img
            src={flagUrl}
            alt={sticker.country_name}
            onError={() => setFlagError(true)}
            className="h-10 w-14 flex-shrink-0 rounded-lg object-cover shadow-sm"
          />
        )}
        <div className="min-w-0 flex-1">
          <p className="text-lg font-bold text-gray-800">
            {sticker.code} · #{sticker.number}
          </p>
          <p className="text-sm text-gray-500">
            {getCountryLabel(sticker.country_name, sticker.country_code)}
          </p>
          <p className="text-sm text-gray-700">{sticker.player_name_or_detail}</p>
        </div>
        <StatusBadge status={sticker.status} />
      </div>

      <div className="flex items-center gap-2 text-sm text-gray-600">
        <span>Cantidad: {sticker.quantity}</span>
        {sticker.repetidas > 0 && <span>· Repetidas: {sticker.repetidas}</span>}
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <ActionButton
          className="bg-pegada text-white"
          icon={IconCheck}
          label={sticker.is_pasted ? "Despegar" : "Pegar"}
          onClick={() => onAction(sticker.id, sticker.is_pasted ? "unpaste" : "paste")}
        />
        <ActionButton
          className="bg-disponible text-white"
          icon={IconPlus}
          label="+1"
          onClick={() => onAction(sticker.id, "increment")}
        />
        <ActionButton
          className="bg-gray-400 text-white"
          icon={IconMinus}
          label="-1"
          onClick={() => onAction(sticker.id, "decrement")}
        />
        <ActionButton
          className="bg-faltante text-white"
          icon={IconAlert}
          label="Marcar faltante"
          onClick={() => onAction(sticker.id, "mark-missing")}
        />
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notas..."
          className="flex-1 rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-green-500 focus:outline-none"
        />
        <button
          type="button"
          onClick={handleSaveNotes}
          disabled={savingNotes}
          className="rounded-xl bg-gray-800 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Guardar
        </button>
      </div>
    </div>
  );
}

function ActionButton({ className, icon: Icon, label, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center justify-center gap-1.5 rounded-xl px-3 py-3 text-sm font-semibold active:opacity-80 ${className}`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}
