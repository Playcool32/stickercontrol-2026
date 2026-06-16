import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  getPublicAlbum,
  getPublicDuplicates,
  getPublicMissing,
  getPublicOwner,
} from "../api/client.js";
import { IconCheck, IconCopy } from "../components/icons.jsx";
import ProgressRing from "../components/ProgressRing.jsx";
import { getCountryLabel } from "../utils/countryLabel.js";

const STATUS_COLOR = {
  FALTANTE: "bg-faltante text-white",
  DISPONIBLE_PARA_PEGAR: "bg-disponible text-white",
  PEGADA_SIN_REPETIDA: "bg-pegada text-white",
  PEGADA_CON_REPETIDA: "bg-repetida text-black",
};

const TABS = ["Álbum", "Faltantes", "Repetidas"];

export default function ShareView() {
  const { token } = useParams();
  const [owner, setOwner] = useState(null);
  const [album, setAlbum] = useState(null);
  const [missing, setMissing] = useState(null);
  const [duplicates, setDuplicates] = useState(null);
  const [activeTab, setActiveTab] = useState("Álbum");
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    getPublicOwner(token)
      .then(setOwner)
      .catch((err) => { if (err.message === "404") setNotFound(true); });
    getPublicAlbum(token)
      .then(setAlbum)
      .catch(() => {});
  }, [token]);

  useEffect(() => {
    if (activeTab === "Faltantes" && !missing) {
      getPublicMissing(token).then(setMissing).catch(() => {});
    }
    if (activeTab === "Repetidas" && !duplicates) {
      getPublicDuplicates(token).then(setDuplicates).catch(() => {});
    }
  }, [activeTab, token, missing, duplicates]);

  if (notFound) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
        <div className="rounded-2xl bg-white p-8 text-center shadow-sm">
          <p className="text-2xl font-bold text-gray-800">Álbum no encontrado</p>
          <p className="mt-2 text-gray-500">Este link no existe o fue desactivado.</p>
        </div>
      </div>
    );
  }

  let summary = null;
  if (album) {
    const all = [...album.groups.flatMap((g) => g.countries), ...album.special];
    const totals = all.reduce(
      (acc, c) => ({
        total: acc.total + c.summary.total,
        pegadas: acc.pegadas + c.summary.pegadas,
        faltantes: acc.faltantes + c.summary.faltantes,
        repetidas: acc.repetidas + c.summary.repetidas,
      }),
      { total: 0, pegadas: 0, faltantes: 0, repetidas: 0 }
    );
    summary = {
      ...totals,
      porcentaje: totals.total
        ? Math.round((totals.pegadas / totals.total) * 1000) / 10
        : 0,
    };
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-100 bg-white p-3">
        <span className="text-sm font-bold text-gray-800">StickerControl 2026</span>
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-semibold text-gray-500">
          Solo lectura
        </span>
      </header>

      <main className="mx-auto w-full max-w-2xl flex-1 p-4 pb-6">
        <div className="mb-4 rounded-2xl bg-gradient-to-br from-green-500 to-green-700 p-6 text-white shadow-lg">
          <p className="text-sm font-semibold text-green-100">
            {owner ? `Álbum de ${owner.owner_name}` : "Cargando…"}
          </p>
          {summary && (
            <div className="mt-4 flex flex-col items-center">
              <ProgressRing
                percentage={summary.porcentaje}
                size={140}
                strokeWidth={12}
                progressColor="#ffffff"
                trackColor="rgba(255,255,255,0.25)"
              >
                <span className="text-3xl font-extrabold">{summary.porcentaje}%</span>
                <span className="mt-1 text-xs text-green-100">
                  {summary.pegadas} / {summary.total} pegadas
                </span>
              </ProgressRing>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center text-xs">
                <div>
                  <p className="text-lg font-bold">{summary.pegadas}</p>
                  <p className="text-green-100">Pegadas</p>
                </div>
                <div>
                  <p className="text-lg font-bold">{summary.faltantes}</p>
                  <p className="text-green-100">Faltantes</p>
                </div>
                <div>
                  <p className="text-lg font-bold">{summary.repetidas}</p>
                  <p className="text-green-100">Repetidas</p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="mb-4 flex gap-2">
          {TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                activeTab === tab
                  ? "bg-green-600 text-white shadow-sm"
                  : "bg-white text-gray-600 shadow-sm"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "Álbum" && <PublicAlbumTab album={album} />}
        {activeTab === "Faltantes" && <PublicMissingTab data={missing} />}
        {activeTab === "Repetidas" && <PublicDuplicatesTab data={duplicates} />}
      </main>
    </div>
  );
}

function PublicAlbumTab({ album }) {
  if (!album) return <p className="text-gray-500">Cargando…</p>;
  return (
    <div className="flex flex-col gap-6">
      {album.special.length > 0 && (
        <section className="flex flex-col gap-3">
          <h3 className="inline-block w-fit rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white">
            Especiales del Mundial
          </h3>
          {album.special.map((country) => (
            <PublicCountryCard key={country.country_code} country={country} />
          ))}
        </section>
      )}
      {album.groups.map((group) => (
        <section key={group.group} className="flex flex-col gap-3">
          <h3 className="inline-block w-fit rounded-full bg-green-600 px-3 py-1 text-sm font-bold text-white">
            Grupo {group.group}
          </h3>
          {group.countries.map((country) => (
            <PublicCountryCard key={country.country_code} country={country} />
          ))}
        </section>
      ))}
    </div>
  );
}

function PublicCountryCard({ country }) {
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
          <div
            key={sticker.id}
            title={`${sticker.code} — ${sticker.player_name_or_detail}`}
            className={`flex h-11 items-center justify-center rounded-lg text-sm font-bold md:h-8 md:text-xs md:font-semibold ${
              STATUS_COLOR[sticker.status] || "bg-gray-200"
            }`}
          >
            {sticker.code === "00" ? "00" : sticker.number}
          </div>
        ))}
      </div>
    </div>
  );
}

function PublicMissingTab({ data }) {
  const [copied, setCopied] = useState(false);
  if (!data) return <p className="text-gray-500">Cargando…</p>;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-4">
      <button
        type="button"
        onClick={handleCopy}
        className="flex items-center justify-center gap-2 rounded-2xl bg-pegada p-4 text-lg font-bold text-white shadow-sm active:opacity-80"
      >
        {copied ? <IconCheck className="h-5 w-5" /> : <IconCopy className="h-5 w-5" />}
        {copied ? "¡Copiado!" : "Copiar para WhatsApp"}
      </button>

      {data.by_country.length === 0 && (
        <p className="rounded-2xl bg-white p-4 text-center text-gray-600 shadow-sm">
          No hay figuritas faltantes.
        </p>
      )}

      {data.by_country.map((country) => (
        <div key={country.country_code} className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="font-bold text-gray-800">
            {country.country_name} ({country.country_code})
          </p>
          <div className="mt-2 grid grid-cols-4 gap-2 md:flex md:flex-wrap md:gap-1">
            {country.numbers.map((number) => (
              <span
                key={number}
                className="flex w-full items-center justify-center rounded-full bg-red-50 px-3 py-3 text-sm font-bold text-faltante md:w-auto md:px-2 md:py-1 md:text-xs md:font-semibold"
              >
                {number === 0 ? "00" : number}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function PublicDuplicatesTab({ data }) {
  const [copied, setCopied] = useState(false);
  if (!data) return <p className="text-gray-500">Cargando…</p>;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-4">
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
          No hay figuritas repetidas.
        </p>
      )}

      {data.by_country.map((country) => (
        <div key={country.country_code} className="rounded-2xl bg-white p-4 shadow-sm">
          <p className="font-bold text-gray-800">
            {country.country_name} ({country.country_code})
          </p>
          <div className="mt-2 grid grid-cols-4 gap-2 md:flex md:flex-wrap md:gap-1">
            {country.items.map((item) => (
              <span
                key={item.number}
                className="flex w-full items-center justify-center rounded-full bg-yellow-50 px-3 py-3 text-sm font-bold text-yellow-700 md:w-auto md:px-2 md:py-1 md:text-xs md:font-semibold"
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
