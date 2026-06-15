// Construye la URL de la bandera a partir del country_code, siguiendo la
// misma convención que /api/reports/album (carpeta public/flags/).
export function getFlagUrl(countryCode) {
  if (!countryCode) return null;
  if (countryCode === "FWC") return "/flags/FWC.svg";
  return `/flags/${countryCode}.png`;
}
