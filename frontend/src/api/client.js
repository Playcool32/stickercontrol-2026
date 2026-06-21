// import.meta.env.BASE_URL incluye la barra final ("/" en dev,
// "/stickercontrol/" en producción), por lo que esto resuelve a "/api" o
// "/stickercontrol/api".
const BASE_URL = `${import.meta.env.BASE_URL}api`;

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    const error = new Error(`${res.status} ${res.statusText}: ${text}`);
    error.status = res.status;
    throw error;
  }

  if (res.status === 204) return null;
  return res.json();
}

export function searchStickers(params = {}) {
  const query = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
  );
  const qs = query.toString();
  return request(`/stickers/search${qs ? `?${qs}` : ""}`);
}

export function pasteSticker(id) {
  return request(`/collection/${id}/paste`, { method: "POST" });
}

export function unpasteSticker(id) {
  return request(`/collection/${id}/unpaste`, { method: "POST" });
}

export function incrementSticker(id) {
  return request(`/collection/${id}/increment`, { method: "POST" });
}

export function decrementSticker(id) {
  return request(`/collection/${id}/decrement`, { method: "POST" });
}

export function markMissing(id) {
  return request(`/collection/${id}/mark-missing`, { method: "POST" });
}

export function updateNotes(id, notes) {
  return request(`/collection/${id}/notes`, {
    method: "PATCH",
    body: JSON.stringify({ notes }),
  });
}

export function bulkMarkCountry(countryCode) {
  return request(`/collection/bulk-mark-country/${countryCode}`, { method: "POST" });
}

export function getAlbum() {
  return request("/reports/album");
}

export function getMissing() {
  return request("/reports/missing");
}

export function getDuplicates() {
  return request("/reports/duplicates");
}

export function getTradesStatus() {
  return request("/trades/status");
}

export function getProfile() {
  return request("/profile");
}

export function updateProfile(data) {
  return request("/profile", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function getNearby() {
  return request("/nearby");
}

export function getContactMessage(userId) {
  return request(`/nearby/${userId}/contact-message`);
}

export function loginWithGoogle(credential) {
  return request("/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export function getMe() {
  return request("/auth/me");
}

export function logout() {
  return request("/auth/logout", { method: "POST" });
}

// --- Fase 2B: link publico de solo lectura ---

export function generateShareToken() {
  return request("/share/generate", { method: "POST" });
}

export function getShareToken() {
  return request("/share/token");
}

const PUBLIC_BASE = `${import.meta.env.BASE_URL}api/public`;

async function publicFetch(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(String(res.status));
  return res.json();
}

export function getPublicOwner(token) {
  return publicFetch(`${PUBLIC_BASE}/${token}`);
}

export function getPublicAlbum(token) {
  return publicFetch(`${PUBLIC_BASE}/${token}/album`);
}

export function getPublicMissing(token) {
  return publicFetch(`${PUBLIC_BASE}/${token}/missing`);
}

export function getPublicDuplicates(token) {
  return publicFetch(`${PUBLIC_BASE}/${token}/duplicates`);
}
