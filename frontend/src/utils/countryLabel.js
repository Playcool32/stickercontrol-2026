// FWC no es una selección/país: es la sección de figuritas especiales del
// Mundial (código 00 + FWC1-FWC19). Donde se mostraría "FIFA World Cup 2026
// (FWC)" como si fuera un país, mostramos esta etiqueta en su lugar.
export function getCountryLabel(countryName, countryCode) {
  if (countryCode === "FWC") return "Especiales FIFA World Cup 2026";
  return `${countryName} (${countryCode})`;
}
