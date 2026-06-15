import { useEffect, useState } from "react";

import { getContactMessage, getNearby, getProfile, updateProfile } from "../api/client.js";
import {
  IconCheck,
  IconCopy,
  IconLocation,
  IconMail,
  IconMapPin,
  IconWhatsApp,
} from "../components/icons.jsx";

const EMPTY_FORM = {
  display_name: "",
  city: "",
  latitude: "",
  longitude: "",
  contact_email: "",
  contact_whatsapp: "",
  is_public: false,
};

function toFormValues(profile) {
  return {
    display_name: profile.display_name ?? "",
    city: profile.city ?? "",
    latitude: profile.latitude ?? "",
    longitude: profile.longitude ?? "",
    contact_email: profile.contact_email ?? "",
    contact_whatsapp: profile.contact_whatsapp ?? "",
    is_public: profile.is_public,
  };
}

export default function Nearby() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [profileError, setProfileError] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [locating, setLocating] = useState(false);

  const [nearby, setNearby] = useState(null);
  const [nearbyError, setNearbyError] = useState(null);
  const [messages, setMessages] = useState({});
  const [copiedUserId, setCopiedUserId] = useState(null);

  useEffect(() => {
    getProfile()
      .then((data) => setForm(toFormValues(data)))
      .catch((err) => setProfileError(err.message));
  }, []);

  const loadNearby = () => {
    getNearby()
      .then(setNearby)
      .catch((err) => setNearbyError(err.message));
  };

  useEffect(() => {
    loadNearby();
  }, []);

  const handleChange = (field) => (e) => {
    const value = field === "is_public" ? e.target.checked : e.target.value;
    setForm((f) => ({ ...f, [field]: value }));
    setProfileSaved(false);
  };

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setProfileError("Tu navegador no soporta geolocalización.");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setForm((f) => ({
          ...f,
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        }));
        setLocating(false);
      },
      (err) => {
        setProfileError(`No se pudo obtener tu ubicación: ${err.message}`);
        setLocating(false);
      }
    );
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setSavingProfile(true);
    setProfileError(null);
    try {
      const payload = {
        display_name: form.display_name || null,
        city: form.city || null,
        latitude: form.latitude === "" ? null : Number(form.latitude),
        longitude: form.longitude === "" ? null : Number(form.longitude),
        contact_email: form.contact_email || null,
        contact_whatsapp: form.contact_whatsapp || null,
        is_public: form.is_public,
      };
      const updated = await updateProfile(payload);
      setForm(toFormValues(updated));
      setProfileSaved(true);
      setMessages({});
      loadNearby();
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setSavingProfile(false);
    }
  };

  const getMessage = async (userId) => {
    if (messages[userId]) return messages[userId];
    const message = await getContactMessage(userId);
    setMessages((m) => ({ ...m, [userId]: message }));
    return message;
  };

  const handleCopy = async (userId) => {
    const { text } = await getMessage(userId);
    await navigator.clipboard.writeText(text);
    setCopiedUserId(userId);
    setTimeout(() => setCopiedUserId(null), 2000);
  };

  const handleWhatsapp = async (user) => {
    const { whatsapp_url } = await getMessage(user.user_id);
    if (whatsapp_url) window.open(whatsapp_url, "_blank");
  };

  const handleEmail = async (user) => {
    const { mailto_url } = await getMessage(user.user_id);
    if (mailto_url) window.location.href = mailto_url;
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800">Usuarios cerca</h2>
        <p className="text-sm text-gray-600">
          Encontrá coleccionistas cerca tuyo para intercambiar figuritas. El contacto se hace
          por WhatsApp o email, fuera de la app.
        </p>
      </div>

      <form onSubmit={handleSaveProfile} className="flex flex-col gap-3 rounded-2xl bg-white p-4 shadow-sm">
        <h3 className="text-lg font-bold text-gray-800">Mi perfil</h3>

        <label className="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          Nombre para mostrar
          <input
            type="text"
            value={form.display_name}
            onChange={handleChange("display_name")}
            placeholder="Ej: Fer"
            className="rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          Ciudad
          <input
            type="text"
            value={form.city}
            onChange={handleChange("city")}
            placeholder="Ej: Buenos Aires"
            className="rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
          />
        </label>

        <div className="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          Ubicación aproximada
          <div className="flex gap-2">
            <input
              type="number"
              step="any"
              value={form.latitude}
              onChange={handleChange("latitude")}
              placeholder="Latitud"
              className="w-1/2 rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
            />
            <input
              type="number"
              step="any"
              value={form.longitude}
              onChange={handleChange("longitude")}
              placeholder="Longitud"
              className="w-1/2 rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
            />
          </div>
          <button
            type="button"
            onClick={handleUseLocation}
            disabled={locating}
            className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-disponible p-2 text-sm font-bold text-white disabled:opacity-50"
          >
            <IconLocation className="h-4 w-4" />
            {locating ? "Obteniendo ubicación..." : "Usar mi ubicación"}
          </button>
          <p className="text-xs font-normal text-gray-500">
            No se guarda tu dirección exacta, solo una ubicación aproximada (~1 km) para calcular
            la distancia.
          </p>
        </div>

        <label className="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          Email de contacto
          <input
            type="email"
            value={form.contact_email}
            onChange={handleChange("contact_email")}
            placeholder="tu@email.com"
            className="rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
          />
        </label>

        <label className="flex flex-col gap-1 text-sm font-semibold text-gray-700">
          WhatsApp (con código de país, sin + ni espacios)
          <input
            type="text"
            value={form.contact_whatsapp}
            onChange={handleChange("contact_whatsapp")}
            placeholder="Ej: 5491122334455"
            className="rounded-xl border border-gray-200 p-2 text-base font-normal focus:border-green-500 focus:outline-none"
          />
        </label>

        <label className="flex items-center gap-2 text-sm font-semibold text-gray-700">
          <input type="checkbox" checked={form.is_public} onChange={handleChange("is_public")} />
          Mostrarme a otros coleccionistas cercanos
        </label>

        {profileError && <p className="text-faltante">{profileError}</p>}

        <button
          type="submit"
          disabled={savingProfile}
          className="rounded-xl bg-pegada p-3 text-lg font-bold text-white disabled:opacity-50"
        >
          {savingProfile ? "Guardando..." : profileSaved ? "¡Guardado!" : "Guardar perfil"}
        </button>
      </form>

      <div className="flex flex-col gap-4">
        <h3 className="text-lg font-bold text-gray-800">Coleccionistas cerca</h3>

        {nearbyError && <p className="text-faltante">Error: {nearbyError}</p>}

        {!nearbyError && !nearby && <p className="text-gray-500">Cargando...</p>}

        {nearby && nearby.users.length === 0 && (
          <p className="text-gray-600">
            Todavía no hay otros usuarios públicos cerca. Activá "Mostrarme a otros
            coleccionistas cercanos" y volvé más tarde.
          </p>
        )}

        {nearby?.users.map((user) => (
          <div key={user.user_id} className="rounded-2xl bg-white p-4 shadow-sm">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-lg font-bold text-gray-800">{user.display_name}</p>
                <p className="text-sm text-gray-500">{user.city || "Ciudad no especificada"}</p>
              </div>
              {user.distance_km != null && (
                <span className="flex flex-shrink-0 items-center gap-1 rounded-full bg-green-100 px-3 py-1 text-sm font-bold text-green-700">
                  <IconMapPin className="h-4 w-4" />
                  {user.distance_km} km
                </span>
              )}
            </div>

            <div className="mt-3 flex flex-wrap gap-2 text-xs font-semibold">
              <span className="rounded-full bg-red-50 px-3 py-1 text-faltante">
                Tiene {user.stickers_i_need_that_user_has.length} que me faltan
              </span>
              <span className="rounded-full bg-yellow-50 px-3 py-1 text-yellow-700">
                Le sirven {user.stickers_user_needs_that_i_have.length} de mis repetidas
              </span>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleCopy(user.user_id)}
                className="flex items-center gap-1.5 rounded-xl bg-gray-100 px-3 py-2 text-sm font-bold text-gray-700"
              >
                {copiedUserId === user.user_id ? (
                  <IconCheck className="h-4 w-4" />
                ) : (
                  <IconCopy className="h-4 w-4" />
                )}
                {copiedUserId === user.user_id ? "¡Copiado!" : "Copiar mensaje"}
              </button>

              {user.has_whatsapp && (
                <button
                  type="button"
                  onClick={() => handleWhatsapp(user)}
                  className="flex items-center gap-1.5 rounded-xl bg-green-600 px-3 py-2 text-sm font-bold text-white"
                >
                  <IconWhatsApp className="h-4 w-4" />
                  WhatsApp
                </button>
              )}

              {user.has_email && (
                <button
                  type="button"
                  onClick={() => handleEmail(user)}
                  className="flex items-center gap-1.5 rounded-xl bg-disponible px-3 py-2 text-sm font-bold text-white"
                >
                  <IconMail className="h-4 w-4" />
                  Email
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
