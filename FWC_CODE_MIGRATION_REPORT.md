# Corrección crítica de especiales FWC — FW1-FW19 → FWC1-FWC19 + logo "00"

## 1. Diagnóstico

Dos errores confirmados en el catálogo de especiales (`country_code="FWC"`):

1. Las 19 figuritas especiales FIFA estaban codificadas como `FW1`..`FW19`
   en vez de `FWC1`..`FWC19`. Origen: `scripts/import_master_stickers_from_xlsm.py`
   hardcodeaba `dominant = "FW"` para las filas especiales (`is_special`),
   generando `code = f"{dominant}{number}"` → `FW1`..`FW19`.
2. El logo oficial (código `00`, `number=0`) se mostraba en el Álbum como
   `"0"` porque el tile de `CountryCard` renderizaba directamente
   `{sticker.number}`.

## 2. Cambios implementados

### `backend/stickercontrol.db` (SQLite)
- `UPDATE master_stickers SET code = 'FWC' || substr(code, 3) WHERE code GLOB 'FW[0-9]*'`
  — rename **in-place** de los 19 códigos (`id` 86-104), sin tocar
  `group`, `country_code`, `country_name`, `number`, `player_name_or_detail`
  ni `type`.
- `id`s preservados (86→`FWC1` ... 104→`FWC19`). `user_stickers` no se tocó:
  las 5 filas con estado cargado para esos `sticker_id` (86, 87, 88, 95, 103)
  quedaron **idénticas** antes/después (`quantity`, `is_pasted`, `notes`).
- El código `00` (`id=985`) no fue modificado.

### `data/stickers_master.csv`
- Filas 3-21: columna `code` cambiada de `FW{n}` a `FWC{n}` (n=1..19). Resto
  de columnas sin cambios. Fila 2 (`00`) sin cambios.

### `frontend/src/pages/Album.jsx`
- Único cambio frontend, el estrictamente necesario para mostrar `00`:
  ```jsx
  {sticker.code === "00" ? "00" : sticker.number}
  ```
  (antes: `{sticker.number}`, que para `code="00"` mostraba `"0"`).

### `scripts/import_master_stickers_from_xlsm.py` (corrección de raíz)
- `dominant = "FW"` → `dominant = "FWC"` para filas especiales (`is_special`),
  para que una futura regeneración del CSV desde el `.xlsm` produzca
  directamente `FWC1`..`FWC19` (antes regeneraría el mismo bug).
- Docstring actualizado: ejemplo `FW1 -> "Especial FIFA 1"` →
  `FWC1 -> "Especial FIFA 1"`, y "Especiales FIFA (prefijo FW)" →
  "Especiales FIFA (prefijo FWC)".
- La línea que describe el layout crudo del `.xlsm` (`Fila 7: "Specials" |
  "Fifa" | "00" | FW1 | FW2 | ... | FW19`) **no se modificó**: describe las
  etiquetas tal como están en la hoja de origen, no los códigos generados.

### Documentación / reportes con `FW1`-`FW19`
Actualizados a `FWC1`-`FWC19` (o el código puntual correspondiente):
- `README.md` (descripción del catálogo).
- `PROJECT_STATE.md` (3 menciones: ejemplo de `player_name_or_detail`,
  descripción de especiales FIFA, resumen de verificación de Fase 0.5).
- `TODO.md` (ejemplo de `player_name_or_detail`).
- `GROUP_ORDER_IMPLEMENTATION_REPORT.md` (orden interno de especiales:
  `00, FWC1, FWC2, ..., FWC19`).
- `LOCAL_UX_AUDIT.md` (6 menciones: ejemplos de códigos cargados en la
  auditoría de Fase 0.6.5, ahora `FWC1`/`FWC2`/`FWC3`/`FWC10`).

### Consistencia frontend adicional (sin tocar lógica/estilos)
- `frontend/src/utils/countryLabel.js`: comentario actualizado
  (`código 00 + FWC1-FWC19`).
- `frontend/src/pages/Search.jsx`: ejemplo del mensaje guía
  `"Ej: ARG10, MEX3, FW1, 00"` → `"Ej: ARG10, MEX3, FWC1, 00"` (el código
  `FW1` ya no existe; mantenerlo en el ejemplo hubiera sido confuso).

## 3. No tocado (según restricciones)

- `backend/app/routes/reports.py`, `backend/app/countries.py`,
  `data/countries.json`: orden de grupos/Especiales sin cambios — la
  migración solo modificó la columna `code`, no `country_code` ni `group`.
- `backend/app/routes/nearby.py` ("Usuarios cerca"): sin cambios.
- `seed_db.py`: **no se ejecutó** (hubiera hecho upsert+delete por `code`;
  el rename en SQLite ya deja la DB sincronizada con el CSV actualizado).
- Resto de `Album.jsx` (orden de secciones, `CountryCard`, modal, keys):
  sin cambios.

## 4. Verificaciones

| Verificación | Resultado |
|---|---|
| `npm run build` | `✓ 51 modules transformed` / `✓ built in 2.77s` ✅ |
| Buscar `00` | `total:1`, `"Logo Oficial Mundial 2026"`, `type:"logo"` ✅ |
| Álbum muestra `00` (no `"0"`) | `Album.jsx` tile: `sticker.code === "00" ? "00" : sticker.number` ✅ |
| Buscar `FWC1` | incluye `id:86, code:"FWC1", "Especial FIFA 1"` (11 resultados por substring, igual que antes con `MEX1`/`ARG1`) ✅ |
| Buscar `FWC19` | `total:1`, `id:104, code:"FWC19", "Especial FIFA 19"` ✅ |
| Buscar `FW1` | `total:0` ✅ |
| Faltantes (`/api/reports/missing`) | sección `FWC` con `numbers: [4,5,6,7,8,9,10,11,12,13,14,15,16,17,19]` (códigos `FWC4`..`FWC19` salvo pegados) ✅ |
| Repetidas (`/api/reports/duplicates`) | sección `FWC` con `items: [{number:1, quantity:1}]` (`FWC1`) ✅ |
| Total stickers (`/api/reports/album`) | **980** ✅ |
| Especiales (`special`, orden) | **20**: `00, FWC1, FWC2, ..., FWC19` ✅ |
| `master_stickers` (conteo) | **980**, `0` códigos `FW[0-9]*`, `19` códigos `FWC[0-9]*` ✅ |
| `user_stickers` (estados de las 5 filas afectadas) | idénticos antes/después (`quantity`, `is_pasted`, `notes`) ✅ |

## 5. Riesgos / notas

- Ninguno nuevo. El cambio en `master_stickers` es un `UPDATE` in-place
  (mismo `id`, mismo `country_code`/`group`/`number`), por lo que no afecta
  `user_stickers`, el orden de grupos (Fase 4) ni `/api/nearby`.
- `frontend/dist/assets/*.js` y `frontend/package-lock.json` también
  matchearon el grep de `FW1`/`FW19` pero son falsos positivos / artefactos:
  el primero se regenera con `npm run build` (ya hecho), el segundo es un
  hash SHA-512 que contiene la subcadena `FW1` por azar.
- Conteos de `user_stickers`/`pegadas` en este chequeo (`36`/`28`) son
  mayores a los de `GROUP_ORDER_IMPLEMENTATION_REPORT.md` (`32`/`25`):
  refleja uso normal de la app entre fases, no algo causado por esta
  migración (la migración solo tocó 19 filas de `master_stickers.code`).
