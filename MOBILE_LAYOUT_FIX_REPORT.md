# Fix — columna angosta en Android (basado en `MOBILE_LAYOUT_ROOT_CAUSE.md`)

Implementación del fix identificado en la Fase 2: eliminar el `max-width:
672px` (`max-w-2xl`) y `max-width: 512px` (`max-w-lg`) **incondicionales** del
shell de la app y del modal, y aplicarlos solo a partir de `md:` (≥768px),
para que en mobile (<768px) el contenido ocupe siempre el 100% del ancho
disponible.

## 1. Cambios realizados

### `frontend/src/components/Layout.jsx`

**Línea 26 — `<main>` (contenedor de todas las páginas vía `<Outlet />`)**

```diff
- <main className="mx-auto flex-1 w-full max-w-2xl p-4 pb-24">
+ <main className="w-full flex-1 p-4 pb-24 md:mx-auto md:max-w-2xl">
```

- Mobile (`<768px`): sin `max-width` → `<main>` ocupa el 100% del viewport.
  `p-4` (16px) se mantiene como padding lateral (dentro del rango pedido de
  12-16px).
- Desktop (`≥768px`): se reincorpora `max-w-2xl` (672px) + `mx-auto`,
  reproduciendo exactamente el layout actual (columna centrada de lectura).

**Línea 31 — `<div>` del nav inferior (7 ítems)**

```diff
- <div className="mx-auto grid max-w-2xl grid-cols-7">
+ <div className="mx-auto grid grid-cols-7 md:max-w-2xl">
```

- Mobile: el `<div>` (block-level, dentro de `<nav className="fixed ... left-0 right-0">`)
  ocupa el 100% del ancho por defecto → los 7 íconos se reparten en todo el
  ancho de la pantalla.
- Desktop (`≥768px`): vuelve a quedar acotado a 672px y centrado, igual que
  antes.

### `frontend/src/components/StickerDetailModal.jsx`

**Línea 26 — panel del modal de detalle de figurita**

```diff
- className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-gray-50 p-4 shadow-xl sm:rounded-2xl"
+ className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl bg-gray-50 p-4 shadow-xl sm:rounded-2xl md:max-w-lg"
```

- Mobile: el panel (bottom sheet, `items-end` por el contenedor padre) ya no
  tiene techo de 512px → ocupa el 100% del ancho de pantalla.
- Desktop (`≥768px`): vuelve `max-w-lg` (512px), modal centrado como antes.
- No se tocó el contenedor overlay (`fixed inset-0 ... sm:items-center
  sm:p-4`) ni el comportamiento de apertura/cierre/teclado (`Escape`,
  `onClose`, `StickerCard`).

## 2. Archivos modificados

- `frontend/src/components/Layout.jsx` (2 cambios: `<main>` y nav inferior)
- `frontend/src/components/StickerDetailModal.jsx` (1 cambio: panel del modal)

Ningún otro archivo fue tocado. En particular, **no se modificó**:
backend, rutas de API, `nginx`, configuración de Vite, base de datos,
`Dashboard.jsx`, `Album.jsx`, `Search.jsx`, `Missing.jsx`, `Duplicates.jsx`,
`Nearby.jsx` — estas páginas no tenían `max-width`/`width` propios (ver
`MOBILE_LAYOUT_ROOT_CAUSE.md` §"Selectores relacionados"), por lo que
heredan automáticamente el ancho completo del nuevo `<main>` sin requerir
cambios.

## 3. Experiencia desktop — qué se mantiene igual

A partir de `md:` (≥768px), las clases aplicadas son **exactamente las
mismas que antes** (`max-w-2xl mx-auto` en `<main>` y nav, `max-w-lg` en el
modal), solo que ahora son condicionales en lugar de incondicionales. El
layout, ancho de columna (672px), centrado y modal de detalle en desktop
**no cambian**.

## 4. Build

```
> stickercontrol-2026-frontend@0.1.0 build
> vite build

vite v5.4.21 building for production...
✓ 51 modules transformed.
dist/index.html                 0.52 kB │ gzip:  0.31 kB
dist/assets/index-B0ia1VY0.css  14.77 kB │ gzip:  3.66 kB
dist/assets/index-DCAC8kL8.js   195.05 kB │ gzip: 61.53 kB
✓ built in 2.00s
```

**Resultado: BUILD OK** (sin errores ni warnings). Se verificó que las clases
nuevas (`md:max-w-2xl`, `md:max-w-lg`, `md:mx-auto`) quedaron incluidas en el
CSS generado (`dist/assets/index-B0ia1VY0.css`).

## 5. Validación de rutas (build de producción, `npm run preview`)

Con `vite preview` sirviendo `dist/` bajo `/stickercontrol/` (mismo `base`
que producción):

| Ruta | Resultado |
|---|---|
| `/stickercontrol/` (Home) | `200` |
| `/stickercontrol/buscar` (Buscar) | `200` |
| `/stickercontrol/album` (Álbum) | `200` |
| `/stickercontrol/faltantes` (Faltantes) | `200` |
| `/stickercontrol/repetidas` (Repetidas) | `200` |
| `/stickercontrol/cerca` (Cerca) | `200` |

Todas las rutas solicitadas devuelven `200` con el build nuevo. Esta
validación cubre que el SPA fallback, el `base` de Vite y el bundle siguen
funcionando igual que antes del fix (no se tocó nada relacionado con
routing/build config). **No se corrió el backend en esta sesión** (fuera de
alcance: "no tocar backend/API"), por lo que las páginas que dependen de
`/api/...` (Home, Álbum, Faltantes, Repetidas, Cerca) muestran su estado de
"Cargando..." sin datos en esta validación estática — el objetivo de esta
fase era el layout/CSS, no los datos.

## 6. Impacto esperado en Android

- **Pantallas <768px** (la inmensa mayoría de celulares Android, incluso los
  que antes reportaban `window.innerWidth` entre 672px y 768px y ya sufrían
  el recorte): `<main>` y el nav inferior pasan a ocupar el 100% del ancho.
  Se elimina por completo la franja gris (`bg-gray-50`) a los costados
  descrita en `MOBILE_LAYOUT_ROOT_CAUSE.md`.
- **Padding lateral**: se mantiene `p-4` (16px), dentro del rango pedido
  (12-16px) — el contenido no queda pegado al borde de la pantalla.
- **Modal de detalle (Álbum)**: en mobile, el bottom sheet ahora también
  ocupa el 100% del ancho (antes quedaba acotado a 512px en pantallas
  >512px), consistente con el resto del shell.
- **Pantallas ≥768px** (tablets Android en horizontal, Chrome "escritorio"
  forzado, PC): comportamiento idéntico al actual — columna de 672px
  centrada, modal de 512px centrado.
- **Riesgo residual**: en el rango 768px-672px... (no aplica, 768>672, es un
  único umbral). El nuevo punto de quiebre es **768px** en lugar de "nunca";
  cualquier dispositivo con `window.innerWidth` entre, por ejemplo, 700px y
  767px ahora usará ancho completo (antes quedaba con franjas si superaba
  672px) — esto es el comportamiento buscado, no un riesgo.

## 7. Restricciones respetadas

- No se modificó backend, API, rutas, nginx ni base de datos.
- No se modificó `Dashboard.jsx`, `Album.jsx`, `Search.jsx`,
  `Missing.jsx`, `Duplicates.jsx`, `Nearby.jsx`, `Trades.jsx`,
  `StickerCard.jsx`, `App.jsx`, `vite.config.js`, `index.css`,
  `tailwind.config.js`.
- Cambios acotados exactamente a los 3 selectores identificados en
  `MOBILE_LAYOUT_ROOT_CAUSE.md` (2 en `Layout.jsx`, 1 en
  `StickerDetailModal.jsx`).

## 8. Próximos pasos recomendados

1. Re-deploy del frontend en el VPS: `npm run build` + asegurar que nginx
   sirve el `dist/` regenerado (mismo procedimiento que `DEPLOY.md`).
2. Verificar en el celular Android real (mismo que generó las capturas de
   Fase 2) que las franjas grises desaparecieron en Home/Buscar/Álbum/
   Faltantes/Repetidas/Cerca y que el nav inferior ocupa todo el ancho.
3. Verificar en PC/desktop (≥768px) que el layout centrado de 672px sigue
   igual que antes (sin regresión visual de escritorio).
