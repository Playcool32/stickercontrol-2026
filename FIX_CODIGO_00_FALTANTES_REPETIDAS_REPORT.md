# Fix — código "00" mostrado como "0" en Faltantes/Repetidas

Cambio puntual de presentación, sin refactor. No se modificó backend, DB ni
API.

## 1. Causa raíz

`GET /api/reports/missing` y `GET /api/reports/duplicates` devuelven, para
cada figurita, su **`number`** (entero) — no el `code`. Para la figurita
"Logo Oficial Mundial 2026" (`code="00"`, `id=985`, `country_code="FWC"`),
`number = 0`.

- `Missing.jsx` renderizaba `{number}` directamente → `0`.
- `Duplicates.jsx` renderizaba `{item.number}` (o `${item.number} (x${item.quantity})`)
  directamente → `0` (o `0 (xN)`).

`number = 0` es **único en todo el catálogo** para `code="00"` — todas las
demás figuritas (selecciones `1-20` y especiales `FWC1`-`FWC19`) usan
`number >= 1`. Por lo tanto `number === 0` identifica sin ambigüedad al
código `00`, igual que ya asume `Album.jsx` con
`sticker.code === "00" ? "00" : sticker.number`.

## 2. Cambios realizados

### `frontend/src/pages/Missing.jsx` (línea ~56)

```diff
-                {number}
+                {number === 0 ? "00" : number}
```

### `frontend/src/pages/Duplicates.jsx` (línea ~56)

```diff
-                {item.quantity > 1 ? `${item.number} (x${item.quantity})` : item.number}
+                {(() => {
+                  const label = item.number === 0 ? "00" : item.number;
+                  return item.quantity > 1 ? `${label} (x${item.quantity})` : label;
+                })()}
```

Ambos cambios afectan **únicamente** el badge visual (`<span>`). No se tocó
`id`, `number`, `code`, `data.by_country`, `data.text`, props, keys ni
estructura de los componentes.

## 3. Archivos modificados

- `frontend/src/pages/Missing.jsx`
- `frontend/src/pages/Duplicates.jsx`

No se modificó: backend (`reports.py`, `schemas.py`, `crud.py`), base de
datos, `Album.jsx`, `Search.jsx`, `StickerCard.jsx`, ni ningún otro archivo.

## 4. Build

```
> stickercontrol-2026-frontend@0.1.0 build
> vite build

vite v5.4.21 building for production...
✓ 51 modules transformed.
dist/index.html                 0.52 kB │ gzip:  0.31 kB
dist/assets/index-B0ia1VY0.css  14.77 kB │ gzip:  3.66 kB
dist/assets/index-AsaX4bFt.js   195.09 kB │ gzip: 61.56 kB
✓ built in 3.15s
```

**Resultado: BUILD OK** (sin errores ni warnings).

## 5. Verificación

- **Faltantes / Repetidas (badges)**: con el fix, cualquier entrada con
  `number === 0` (exclusivamente el código `00`) se muestra como `"00"` en
  el badge, idéntico al criterio ya usado en `Album.jsx` para el mismo
  código.
- **Estado de datos local (`backend/stickercontrol.db`, usuario `id=1`)**:
  ```
  master_sticker 00 -> id=985, code='00', number=0, country_code='FWC', group=None
  user_sticker   -> quantity=0, is_pasted=1
  ```
  Con `quantity=0` y `is_pasted=1`, el status de `00` es
  `PEGADA_SIN_REPETIDA` (ni `FALTANTE` ni `repetidas>0`), por lo que **en
  este dataset local, `00` no aparece hoy ni en Faltantes ni en
  Repetidas** — no se pudo reproducir visualmente con datos reales en esta
  sesión. El fix aplicado es una condición aislada (`number === 0 ? "00" :
  number`) que se activa apenas `00` pase a estado `FALTANTE` o tenga
  `repetidas > 0` (ej. en el entorno de producción, donde el reporte
  original detectó el bug).

- **Copiar al portapapeles / Texto WhatsApp (`data.text`)**: ⚠️ **hallazgo
  adicional, no corregido (fuera de alcance)**. `data.text` es generado
  **en el backend** (`backend/app/routes/reports.py`,
  `get_missing`/`get_duplicates`), a partir del mismo `sticker.number`:
  ```python
  lines.append(f"{country_code}: " + ", ".join(str(n) for n in numbers))
  ```
  Para `code="00"`, esto produce literalmente `"FWC: 0, ..."` (o
  `"FWC: 0(x2), ..."` en Repetidas), no `"00"`. Como el botón "Copiar para
  WhatsApp" usa `navigator.clipboard.writeText(data.text)` **directamente**
  (sin pasar por los badges), el texto copiado seguiría mostrando `0` para
  esa entrada, aunque el badge en pantalla ahora muestre `00`.

  Esto **no se corrigió** porque requiere modificar `reports.py`
  (backend/API), explícitamente fuera de alcance de este cambio
  ("sin modificar backend, DB ni API"). Queda documentado como
  inconsistencia conocida: pantalla muestra `00`, texto copiado/WhatsApp
  mostraría `0` para esa misma figurita, hasta que se aborde en una fase
  futura con cambio de backend.

## 6. Resumen

| Ítem | Estado |
|---|---|
| Badge "Faltantes" (`Missing.jsx`) | ✅ corregido |
| Badge "Repetidas" (`Duplicates.jsx`) | ✅ corregido |
| `id=1`, `number=0`, `code="00"` | sin cambios (verificado) |
| Backend / DB / API | sin cambios |
| Build | ✅ OK |
| Texto WhatsApp / portapapeles (`data.text`) | ⚠️ no corregido — requiere cambio de backend, fuera de alcance; documentado como follow-up |
