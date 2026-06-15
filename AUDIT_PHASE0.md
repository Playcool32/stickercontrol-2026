# Auditoría Fase 0 — StickerControl 2026

Fecha: 2026-06-14
Alcance: `stickercontrol-2026/` (Fase 0, MVP local sin login). Auditoría de
solo lectura — no se modificó código de la aplicación.

## 1. Backend arranca desde cero

**Resultado: OK**

- `cd backend && .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000`
  arranca limpio:
  ```
  INFO:     Started server process [...]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://127.0.0.1:8000
  ```
- `GET /` responde `{"status":"ok","app":"StickerControl 2026"}`.
- Dependencias instaladas (`requirements.txt`) coinciden exactamente con
  las versiones presentes en `.venv` (fastapi 0.115.0, sqlalchemy 2.0.35,
  pydantic 2.9.2, uvicorn 0.30.6, python-dotenv 1.0.1).
- `python-dotenv` se usa efectivamente (`database.py` llama a
  `load_dotenv(BACKEND_DIR / ".env")`), aunque no exista `.env` en Fase 0
  (solo `.env.example`, correcto).

## 2. Frontend arranca desde cero

**Resultado: OK**

- `npm run build` (producción): `44 modules transformed`, build en ~1.7s,
  **sin errores ni warnings**. Genera `dist/` (gitignored).
- `npm run dev`: Vite listo en ~0.5s, sirve en `http://localhost:5173`.
- Proxy `/api/*` → `http://localhost:8000` verificado
  (`GET /api/trades/status` vía `:5173` responde 200).
- Banderas estáticas (`/flags/*.png`, `/flags/FWC.svg`) servidas
  correctamente.
- `npm install` reporta **2 vulnerabilidades (1 moderate, 1 high)** en
  `esbuild`/`vite` (dependencias de desarrollo, afectan solo al dev
  server). Ver sección 5.

## 3. SQLite se crea automáticamente

**Resultado: OK**

Probado de forma aislada con `DATABASE_URL` apuntando a un archivo SQLite
inexistente: `init_db()` (llamado en el evento `startup` de
`app/main.py`):

- Crea el archivo `.db` si no existe.
- Crea las 3 tablas: `users`, `master_stickers`, `user_stickers`.
- Inserta automáticamente el usuario local por defecto
  (`id=1`, `local@stickercontrol.local`, "Coleccionista Local").
- `master_stickers` y `user_stickers` quedan **vacías** hasta correr
  `seed_db.py` — comportamiento esperado y documentado.

La base real del proyecto (`backend/stickercontrol.db`) no fue tocada
durante esta prueba (se usó un archivo temporal aparte, eliminado al
finalizar).

## 4. Todas las rutas funcionan

**Resultado: OK — 12/12 rutas probadas**

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/` | 200, health check |
| GET | `/api/stickers/search` | 200, probado con `q`, `group`, `country_code`, `type`, búsqueda numérica |
| POST | `/api/collection/{id}/paste` | 200, cambia `is_pasted=true` |
| POST | `/api/collection/{id}/unpaste` | 200, cambia `is_pasted=false` |
| POST | `/api/collection/{id}/increment` | 200, `quantity += 1` |
| POST | `/api/collection/{id}/decrement` | 200, `quantity = max(q-1, 0)`; probado en 0 → se mantiene en 0 |
| POST | `/api/collection/{id}/mark-missing` | 200, `quantity=0, is_pasted=false` |
| PATCH | `/api/collection/{id}/notes` | 200, guarda y limpia notas |
| GET | `/api/reports/album` | 200, devuelve grupos A/C/H/J + especiales (FWC) |
| GET | `/api/reports/missing` | 200 |
| GET | `/api/reports/duplicates` | 200 |
| GET | `/api/trades/status` | 200, `{"implemented": false, "phase": "futura - intercambios"}` |

Casos de error:
- `POST /api/collection/99999/paste` y `PATCH /api/collection/99999/notes`
  → `404 Sticker no encontrado` (sticker inexistente).
- `GET /api/nonexistent` → `404` (FastAPI default).

Acciones de prueba sobre `ARG10` (id=70) revertidas al finalizar
(increment→decrement, paste→unpaste, notes→null), por lo que el estado de
`user_stickers` quedó funcionalmente igual, salvo un detalle descrito en
§5.

Búsqueda `q=20` devuelve 5 resultados (`ARG20`, `BRA20`, `ESP20`, `MEX20` por
`number=20`, y `FWC1` porque su `player_name_or_detail` = "Logo Oficial
Mundial **2026**" matchea `ILIKE '%20%'`). Es el comportamiento esperado de
la búsqueda por texto (no es un bug), pero puede sorprender si se espera
búsqueda exacta por número.

## 5. Errores, TODOs, placeholders y deuda técnica

- **Sin marcadores `TODO`/`FIXME`/`XXX`/`HACK`** en código propio (solo
  aparecen dentro de `backend/.venv/...`, que es código de terceros).
- **Placeholders documentados (esperados en Fase 0)**:
  - `backend/app/auth.py`: `get_current_user_id()` devuelve `1` fijo,
    docstring explica el reemplazo en Fase 1.
  - `backend/app/routes/trades.py`: único endpoint `GET /status` →
    `{"implemented": false, ...}`, sin lógica de intercambios.
  - `frontend/src/pages/Trades.jsx`: página "Próximamente".
- **Código muerto menor**: `getTradesStatus()` está exportado en
  `frontend/src/api/client.js` pero no se usa en ningún componente
  (`Trades.jsx` no lo llama). No rompe nada, pero es función sin uso.
- **Shadowing de builtin**: en `backend/app/routes/stickers.py`, el
  parámetro de query `type: str | None` tapa el builtin `type` de Python
  dentro de la función `search_stickers`. Funciona correctamente (se usa
  `type.lower()` antes de filtrar), pero es un nombre a evitar si se
  refactoriza.
- **`PATCH /api/collection/{id}/notes` sin body o con `{}`**: `NotesUpdate.notes`
  tiene default `None`, así que un PATCH sin el campo `notes` **borra** la
  nota existente (la pone en `null`). El frontend actual siempre envía el
  valor del input, así que no se dispara, pero es un detalle a tener en
  cuenta si se agregan más clientes de la API.
- **`user_stickers` acumula filas "sin cambios"**: `get_or_create_user_sticker`
  crea una fila la primera vez que se llama a *cualquier* acción sobre una
  figurita, aunque el resultado neto sea igual al estado por defecto
  (`quantity=0, is_pasted=false, notes=null`). Ejemplo encontrado durante
  esta auditoría: tras probar `increment`→`decrement` y
  `paste`→`unpaste` sobre `ARG10` (id=70), quedó una fila nueva
  `(user_id=1, sticker_id=70, quantity=0, is_pasted=0, notes=NULL)` en
  `user_stickers` que no existía antes. No afecta el estado/álbum
  (sigue viéndose como `FALTANTE`), pero la tabla crecerá con filas
  "vacías" a medida que el usuario interactúa con figuritas sin cambiar su
  estado final.
- **Vulnerabilidades npm (dev-only)**: `npm audit` reporta 1 alta y 1
  moderada, ambas en `esbuild`/`vite` (servidor de desarrollo). Afectan
  solo a `npm run dev` en localhost; no se usan en el build de producción
  servido por nginx. Pendiente de revisar si se expone el dev server a una
  red no confiable.
- **Dataset de prueba**: `data/stickers_master.csv` (85 filas: MEX, BRA,
  ESP, ARG + FWC) está explícitamente documentado como dataset de PRUEBA en
  `README.md`, `PROJECT_STATE.md`, `TODO.md` y en el docstring de
  `MasterSticker` — pendiente de reemplazo por el catálogo real (~970
  figuritas), ya trackeado en `TODO.md` (Fase 0 pendiente / Fase 3).
- **`frontend/dist/`**: generado durante esta auditoría al correr
  `npm run build` para verificar que compila sin errores. Está
  correctamente listado en `.gitignore` (`frontend/dist/`), pero queda en
  disco. No requiere acción salvo borrarlo si se quiere dejar el working
  tree exactamente como antes de la auditoría.

## 6. Archivos huérfanos

**Resultado: ninguno encontrado.**

- Todos los módulos del backend (`auth.py`, `countries.py`, `crud.py`,
  `status.py`, `database.py`, `models.py`, `schemas.py`, los 4 routers) son
  importados y usados desde `main.py` o entre sí.
- Todos los componentes/páginas del frontend (`Layout`, `StickerCard`,
  `StatusBadge`, y las 6 páginas) están importados desde `App.jsx` o entre
  componentes.
- `data/countries.json` es usado por `backend/app/countries.py`
  (`get_flag_path`, para el álbum).
- `data/stickers_master.csv` es usado por `backend/seed_db.py`.
- `scripts/sync_country_assets.py` es la única utilidad en `scripts/` y
  cumple su propósito documentado (copiar países/banderas desde el
  proyecto padre).
- No se encontraron archivos `.env` reales (solo `.env.example` en
  `backend/` y `frontend/`), consistente con que no hay secretos
  commiteados.
- `backend/__pycache__/*.pyc`, `backend/.venv/`, `frontend/node_modules/`
  y `backend/stickercontrol.db` existen en disco pero están correctamente
  excluidos por `.gitignore`.

## Conclusión

Fase 0 funciona end-to-end tal como está documentada: backend y frontend
arrancan desde cero sin errores, SQLite se autogenera con el usuario local
y las tablas vacías, las 12 rutas de la API responden correctamente
(incluyendo casos 404), y no hay archivos huérfanos ni código sin usar
relevante (salvo el `getTradesStatus()` sin consumir, de bajo impacto). Los
puntos de deuda técnica listados en §5 son menores y ya están, en su
mayoría, anticipados en `TODO.md`/`PROJECT_STATE.md` como pendientes de
fases futuras.
