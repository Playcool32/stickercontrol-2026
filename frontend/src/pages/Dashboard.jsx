import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getAlbum } from "../api/client.js";
import ProgressRing from "../components/ProgressRing.jsx";
import {
  IconAlbum,
  IconAlert,
  IconLayers,
  IconMapPin,
  IconSearch,
} from "../components/icons.jsx";

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [countries, setCountries] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    getAlbum()
      .then((data) => {
        const groupCountries = data.groups.flatMap((g) => g.countries);
        const allCountries = [...groupCountries, ...data.special];
        const totals = allCountries.reduce(
          (acc, c) => ({
            total: acc.total + c.summary.total,
            pegadas: acc.pegadas + c.summary.pegadas,
            faltantes: acc.faltantes + c.summary.faltantes,
            repetidas: acc.repetidas + c.summary.repetidas,
          }),
          { total: 0, pegadas: 0, faltantes: 0, repetidas: 0 }
        );
        const porcentaje = totals.total
          ? Math.round((totals.pegadas / totals.total) * 1000) / 10
          : 0;
        const selecciones = groupCountries.length;
        const especiales = data.special.reduce((sum, c) => sum + c.summary.total, 0);
        setSummary({ ...totals, porcentaje, selecciones, especiales });
        setCountries(groupCountries.filter((c) => c.flag));
      })
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl bg-gradient-to-br from-green-500 to-green-700 p-6 text-white shadow-lg">
        <p className="text-sm font-semibold uppercase tracking-wide text-green-100">
          StickerControl 2026
        </p>
        <h1 className="text-xl font-bold">Mi álbum del Mundial</h1>

        {error && <p className="mt-3 text-sm text-red-100">Error: {error}</p>}

        {summary && (
          <div className="mt-4 flex flex-col items-center">
            <ProgressRing
              percentage={summary.porcentaje}
              size={168}
              strokeWidth={14}
              progressColor="#ffffff"
              trackColor="rgba(255,255,255,0.25)"
            >
              <span className="text-3xl font-extrabold">{summary.porcentaje}%</span>
              <span className="mt-1 text-xs text-green-100">
                {summary.pegadas} / {summary.total} pegadas
              </span>
            </ProgressRing>
          </div>
        )}
      </div>

      {countries.length > 0 && (
        <Link to="/album" className="block rounded-2xl bg-white p-3 shadow-sm">
          <p className="mb-2 px-1 text-xs font-semibold text-gray-500">
            {summary.selecciones} selecciones
            {summary.especiales > 0 && ` · ${summary.especiales} especiales del Mundial`}
          </p>
          <div className="flex gap-3 overflow-x-auto">
            {countries.map((c) => (
              <div
                key={c.country_code}
                className="flex flex-shrink-0 flex-col items-center gap-1"
              >
                <img
                  src={c.flag}
                  alt={c.country_name}
                  className="h-8 w-12 rounded object-cover shadow-sm"
                />
                <span className="text-[10px] font-semibold text-gray-500">
                  {c.country_code}
                </span>
              </div>
            ))}
          </div>
        </Link>
      )}

      {summary && (
        <div className="grid grid-cols-3 gap-3">
          <StatCard label="Pegadas" value={summary.pegadas} color="text-pegada" bg="bg-green-50" />
          <StatCard label="Faltantes" value={summary.faltantes} color="text-faltante" bg="bg-red-50" />
          <StatCard label="Repetidas" value={summary.repetidas} color="text-repetida" bg="bg-yellow-50" />
        </div>
      )}

      <div>
        <h2 className="mb-2 text-lg font-bold text-gray-800">Accesos rápidos</h2>
        <div className="grid grid-cols-2 gap-3">
          <QuickLink to="/buscar" label="Buscar" icon={IconSearch} />
          <QuickLink to="/album" label="Álbum" icon={IconAlbum} />
          <QuickLink to="/faltantes" label="Faltantes" icon={IconAlert} />
          <QuickLink to="/repetidas" label="Repetidas" icon={IconLayers} />
          <QuickLink to="/cerca" label="Usuarios cerca" icon={IconMapPin} className="col-span-2" />
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color, bg }) {
  return (
    <div className={`rounded-xl ${bg} p-4 text-center shadow-sm`}>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-gray-600">{label}</p>
    </div>
  );
}

function QuickLink({ to, label, icon: Icon, className = "" }) {
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 rounded-xl bg-white p-4 shadow-sm transition-transform active:scale-[0.98] ${className}`}
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
        <Icon className="h-5 w-5" />
      </span>
      <span className="font-semibold text-gray-800">{label}</span>
    </Link>
  );
}
