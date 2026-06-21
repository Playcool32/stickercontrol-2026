# Auditoría — Carga masiva por país (Fase 2C)

## 1. Arquitectura actual relevante

- `user_stickers` (`backend/app/models.py:68`) guarda el estado por figurita y usuario: `quantity`, `is_pasted`, `notes`. Una fila por `(user_id, sticker_id)`, creada on-demand.
- `get_or_create_user_sticker(db, user_id, sticker_id)` (`backend/app/crud.py:67`) es el único punto que crea/recupera esa fila. Si no existe, la crea con `quantity=0, is_pasted=False` y hace `db.flush()` (sin commit).
- Todos los endpoints de colección (`backend/app/routes/collection.py`) siguen el mismo patrón: `_get_master_sticker` → `get_or_create_user_sticker` → mutar 1-2 campos → `_respond` (que hace `db.commit()` + `db.refresh()`).
- Los reportes (`/api/reports/album|missing|duplicates`, `backend/app/routes/reports.py`) y el share público (`backend/app/routes/share.py`) **no tienen estado propio**: recalculan todo en cada request leyendo `user_stickers` vía `_all_stickers_with_status()`. Esto significa que una carga masiva no requiere ningún cambio en reportes ni en share — se reflejan solos en el siguiente `GET`.
- `status.py` define las reglas de estado: `is_pasted=True` con `quantity` preservado → `PEGADA_CON_REPETIDA` si `quantity>=1`, o `PEGADA_SIN_REPETIDA` si `quantity=0`. Es decir, **marcar como pegada nunca borra repetidas**, porque `quantity` no se toca.
- Filtrar figuritas por país ya existe en `stickers.py` (`country_code` uppercased) y en `models.MasterSticker.country_code` (indexado).

## 2. Endpoints existentes de colección / lógica de update

| Endpoint | Efecto |
|---|---|
| `POST /api/collection/{id}/paste` | `is_pasted=True`, no toca `quantity`/`notes` |
| `POST /api/collection/{id}/unpaste` | `is_pasted=False` |
| `POST /api/collection/{id}/increment` / `decrement` | `quantity` ± 1 |
| `POST /api/collection/{id}/mark-missing` | `quantity=0, is_pasted=False` (reset total) |
| `PATCH /api/collection/{id}/notes` | `notes` |

No existe ningún endpoint que opere sobre más de un sticker a la vez. La carga masiva por país es funcionalmente equivalente a aplicar `paste` a cada figurita de un país, pero hecho en una sola transacción.

## 3. Impacto en reportes, share público y repetidas

- **Reportes** (`/album`, `/missing`, `/duplicates`): sin cambios de código necesarios. Se recalculan en cada `GET` desde `user_stickers`; en cuanto el bulk-mark hace commit, el siguiente `getAlbum()` del frontend ya refleja el país completo.
- **Share público**: mismo motivo — `share.py` reutiliza `_all_stickers_with_status` de `reports.py`. Nada que tocar.
- **Repetidas**: como el bulk-mark solo toca `is_pasted` y nunca `quantity`, una figurita con `quantity=2` que se marca como pegada pasa a `PEGADA_CON_REPETIDA` con `repetidas=2` — exactamente la regla ya usada por `paste_sticker` individual. No hay caso nuevo a manejar.
- **Otros usuarios**: la query siempre filtra por `user_id` (vía `get_current_user_id` y `get_or_create_user_sticker`), igual que el resto de endpoints. No hay riesgo de fuga entre usuarios.
- **`master_stickers`**: no se toca, es solo lectura (catálogo).

## 4. Archivos a modificar

- `backend/app/routes/collection.py` — nuevo endpoint `POST /api/collection/bulk-mark-country/{country_code}`.
- `backend/app/crud.py` — opcional: helper para traer los `MasterSticker` de un país (o query directa en el endpoint; el país siempre cabe en una sola query, no justifica un helper nuevo).
- `backend/app/schemas.py` — nuevo schema de respuesta simple (`BulkMarkCountryResponse`: `country_code`, `marked`, `total`).
- `frontend/src/api/client.js` — nueva función `bulkMarkCountry(countryCode)`.
- `frontend/src/pages/Album.jsx` — botón "Marcar selección completa" en `CountryCard`, con confirmación y reload del álbum tras éxito.

No se requiere migración de base de datos: no hay columnas nuevas, solo se reutiliza `user_stickers` tal como existe hoy.

## 5. Diseño propuesto (el más simple posible)

**Backend:**

```
POST /api/collection/bulk-mark-country/{country_code}
```

- Requiere sesión (`get_current_user_id`), igual que el resto de `/api/collection`.
- Busca todos los `MasterSticker` con `country_code == country_code.upper()`. Si no hay ninguno → 404 (país inexistente), igual criterio que `_get_master_sticker`.
- Para cada uno: `get_or_create_user_sticker(db, user_id, sticker.id)` y `entry.is_pasted = True` (sin tocar `quantity` ni `notes`).
- Un solo `db.commit()` al final (no uno por figurita, para que sea atómico: o se marca el país completo o no se marca nada si algo falla).
- Devuelve `{country_code, marked: <cantidad actualizada>, total: <cantidad de figuritas del país>}` (count informativo, no estado completo del país — el frontend ya tiene `getAlbum()` para refrescar).

**Frontend:**

- Botón "Marcar selección completa" en el header de cada `CountryCard` de `Album.jsx`, al lado del nombre del país.
- Al click: `window.confirm` con el texto pedido, usando `summary.total` real del país (no hardcodear "20"): *"Vas a marcar las {total} figuritas de {country_code} como pegadas. No se perderán notas ni repetidas. ¿Continuar?"*
- Si confirma: llama `bulkMarkCountry(country_code)`, luego `loadAlbum()` (mismo patrón que `handleAction`).
- No se agrega esto a `Search.jsx`/`Missing.jsx`/`Duplicates.jsx` en este MVP: el pedido es "botón por país", y `Album.jsx` es la única vista donde el país aparece como unidad visual completa (`CountryCard`). Mantener el alcance acotado a un solo lugar reduce superficie de cambio y riesgo.

## 6. Riesgos

- **Bajo en general.** La operación es additiva sobre filas existentes, usa la misma función de creación (`get_or_create_user_sticker`) que ya está probada por el resto de endpoints, y no introduce estado nuevo ni tablas nuevas.
- Confirmar antes de aplicar es obligatorio (ya lo pide el spec) porque es la única acción que afecta >1 figurita a la vez sin un "undo" dedicado — la reversión es manual, figurita por figurita, igual que cualquier otro estado hoy.
- Países "especiales" (`group=None`, ej. FWC) también tienen `country_code` (ej. `FWC`) y `CountryCard` los renderiza igual que un país de grupo — el endpoint funciona igual para ellos sin caso especial.
- Si el usuario hace bulk-mark dos veces seguidas sobre el mismo país, es idempotente (vuelve a poner `is_pasted=True` en lo que ya estaba en `True`), sin efectos secundarios.
- Ningún riesgo de concurrencia entre usuarios distintos (todo queda filtrado por `user_id`), ni de afectar `master_stickers` o el share público de otro usuario.

## 7. Estimación

**Baja.** ~1-2 horas: un endpoint backend (~15 líneas reutilizando patrones existentes), un schema nuevo, una función de cliente, y un botón + confirm en un solo componente frontend ya existente (`CountryCard` dentro de `Album.jsx`). No hay migración, no hay nuevas dependencias, no hay cambios en reportes/share (se heredan gratis).

## 8. Compatibilidad con datos existentes

- 100% compatible. No cambia el esquema de `user_stickers`, no reinterpreta datos viejos, no requiere backfill.
- Usuarios sin ninguna fila en `user_stickers` para un país (caso normal: usuario nuevo) se comportan igual que con `paste` individual: se crean las filas faltantes con `quantity=0, is_pasted=True`.
- `quantity` y `notes` de figuritas que ya estaban marcadas (pegadas o no) se preservan sin excepción, porque el endpoint nunca las toca.

## 9. Conclusión de la auditoría

**Riesgo bajo → se procede a implementar el MVP descrito en la sección 5**, respetando el alcance exacto pedido: un botón por país, confirmación previa, sin tocar otros usuarios ni `master_stickers`, reportes y share actualizados automáticamente por diseño.
