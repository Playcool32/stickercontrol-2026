import {
  decrementSticker,
  incrementSticker,
  markMissing,
  pasteSticker,
  unpasteSticker,
} from "./client.js";

// Mapa compartido acción -> llamada API, usado por Buscar y Álbum para
// aplicar la misma lógica de colección sobre un StickerCard.
export const STICKER_ACTIONS = {
  paste: pasteSticker,
  unpaste: unpasteSticker,
  increment: incrementSticker,
  decrement: decrementSticker,
  "mark-missing": markMissing,
};
