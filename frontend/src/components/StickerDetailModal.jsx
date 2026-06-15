import { useEffect } from "react";

import StickerCard from "./StickerCard.jsx";
import { IconX } from "./icons.jsx";

// Envuelve el mismo StickerCard que usa Buscar en un panel modal, para que
// el Álbum pueda abrir el detalle/acciones de una figurita sin duplicar UI.
export default function StickerDetailModal({ sticker, onClose, onAction, onSaveNotes }) {
  useEffect(() => {
    if (!sticker) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [sticker, onClose]);

  if (!sticker) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-gray-50 p-4 shadow-xl sm:rounded-2xl md:max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-2 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar"
            className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 text-gray-600 active:opacity-80"
          >
            <IconX className="h-4 w-4" />
          </button>
        </div>
        <StickerCard sticker={sticker} onAction={onAction} onSaveNotes={onSaveNotes} />
      </div>
    </div>
  );
}
