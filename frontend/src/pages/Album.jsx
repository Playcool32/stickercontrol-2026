import { useEffect, useState } from "react";

import { getAlbum, updateNotes } from "../api/client.js";
import { STICKER_ACTIONS } from "../api/stickerActions.js";
import ProgressRing from "../components/ProgressRing.jsx";
import StickerDetailModal from "../components/StickerDetailModal.jsx";
import { getCountryLabel } from "../utils/countryLabel.js";

const STATUS_COLOR = {
  FALTANTE: "bg-faltante text-white",
  DISPONIBLE_PARA_PEGAR: "bg-disponible text-white",
  PEGADA_SIN_REPETIDA: "bg-pegada text-white",
  PEGADA_CON_REPETIDA: "bg-repetida text-black",
};

export default function Album() {
  const [album, setAlbum] = useState(null);
  const [error, setError] = useState(null);
  const [selectedSticker, setSelectedSticker] = useState(null);

  const loadAlbum = () => {
    getAlbum()
      .then(setAlbum)
      .catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadAlbum();
  }, []);

  const handleAction = async (id, action) => {
    try {
      const updated = await STICKER_ACTIONS[action](id);
      setSelectedSticker(updated);
      loadAlbum();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSaveNotes = async (id, notes) => {
    try {
      const updated = await updateNotes(id, notes);
      setSelectedSticker(updated);
    } catch (err) {
      setError(err.message);
    }
  };

  if (error) return <p className="text-faltante">Error: {error}</p>;
  if (!album) return <p className="text-gray-500">Cargando...</p>;

  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-bold text-gray-800">Álbum</h2>

      {album.special.length > 0 && (
        <section className="flex flex-col gap-3">
          <h3 className="inline-block w-fit rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white">
            Especiales del Mundial
          </h3>
          {album.special.map((country) => (
            <CountryCard key={country.country_code} country={country} onSelectSticker={setSelectedSticker} />
          ))}
        </section>
      )}

      {album.groups.map((group) => (
        <section key={group.group} className="flex flex-col gap-3">
          <h3 className="inline-block w-fit rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white">
            Grupo {group.group}
          </h3>
          {group.countries.map((country) => (
            <CountryCard key={country.country_code} country={country} onSelectSticker={setSelectedSticker} />
          ))}
        </section>
      ))}

      <StickerDetailModal
        sticker={selectedSticker}
        onClose={() => setSelectedSticker(null)}
        onAction={handleAction}
        onSaveNotes={handleSaveNotes}
      />
    </div>
  );
}

function CountryCard({ country, onSelectSticker }) {
  const { summary } = country;
  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        {country.flag && (
          <img
            src={country.flag}
            alt={country.country_name}
            className="h-10 w-14 flex-shrink-0 rounded-lg object-cover shadow-sm"
          />
        )}
        <div className="min-w-0 flex-1">
          <p className="truncate font-bold text-gray-800">
            {getCountryLabel(country.country_name, country.country_code)}
          </p>
          <div className="hidden md:block">
            <p className="text-xs text-gray-500">
              {summary.pegadas}/{summary.total} pegadas
            </p>
            <p className="mt-0.5 text-xs">
              <span className="font-semibold text-faltante">{summary.faltantes} faltantes</span>
              {" · "}
              <span className="font-semibold text-yellow-600">{summary.repetidas} repetidas</span>
            </p>
          </div>
        </div>
        <ProgressRing
          percentage={summary.porcentaje}
          size={56}
          strokeWidth={6}
          progressColor="#22c55e"
          trackColor="#e5e7eb"
        >
          <span className="text-sm font-bold text-gray-700">{summary.porcentaje}%</span>
        </ProgressRing>
      </div>

      <div className="mt-2 md:hidden">
        <p className="text-sm text-gray-500">
          {summary.pegadas}/{summary.total} pegadas
        </p>
        <p className="mt-0.5 text-sm">
          <span className="font-semibold text-faltante">{summary.faltantes} faltantes</span>
          {" · "}
          <span className="font-semibold text-yellow-600">{summary.repetidas} repetidas</span>
        </p>
      </div>

      <div className="mt-3 grid grid-cols-5 gap-2 md:grid-cols-10 md:gap-1">
        {country.stickers.map((sticker) => (
          <button
            key={sticker.id}
            type="button"
            title={`${sticker.code} - ${sticker.player_name_or_detail}`}
            onClick={() => onSelectSticker(sticker)}
            className={`flex h-11 items-center justify-center rounded-lg text-sm font-bold transition-transform active:scale-90 md:h-8 md:text-xs md:font-semibold ${STATUS_COLOR[sticker.status] || "bg-gray-200"}`}
          >
            {sticker.code === "00" ? "00" : sticker.number}
          </button>
        ))}
      </div>
    </div>
  );
}
