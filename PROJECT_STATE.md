# Estado del proyecto

## Fase actual: Fase 0.6.2 — Preparación para deploy bajo SkillGames

Decisión explícita del usuario: **sin Google OAuth, multi-usuario, login,
chat ni invitaciones todavía**. La app corre con un único usuario implícito
(`id=1`).

### Fase 0.6.2 — Preparación para deploy bajo SkillGames (actual)

Objetivo: que la app funcione bajo
`https://www.skillgames.com.ar/stickercontrol`, sin agregar login, chat,
OAuth ni invitaciones. Cambios:

- **Bug de privacidad corregido (B1, detectado en la auditoría forense
  [`NEARBY_FORENSIC_TEST.md`](./NEARBY_FORENSIC_TEST.md))**:
  `GET /api/nearby/{user_id}/contact-message` devuelve `404` con el mismo
  detalle (`"Usuario no encontrado"`) tanto si el usuario no existe como si
  no tiene `is_public=true`, para no revelar la existencia de perfiles
  privados.
- **`/api/nearby` ya no expone `contact_email`/`contact_whatsapp` en texto
  plano**: `NearbyUser` ahora tiene `has_email`/`has_whatsapp` (booleanos).
  `ContactMessageResponse` genera `whatsapp_url` y `mailto_url` en el
  servidor (con `urllib.parse.quote`), listos para usar desde el frontend.
- **`frontend/vite.config.js`**: `base` depende de `mode`
  (`"/stickercontrol/"` en producción —`vite build`—, `"/"` en desarrollo).
- **`frontend/src/main.jsx`**: `BrowserRouter` recibe
  `basename={import.meta.env.BASE_URL.replace(/\/$/, "")}` (vacío en dev,
  `/stickercontrol` en producción). No se modificaron `App.jsx` ni
  `Layout.jsx` — las rutas internas siguen siendo relativas.
- **`frontend/src/api/client.js`**: `BASE_URL = `${import.meta.env.BASE_URL}api``
  → `/api` en dev (proxy de Vite), `/stickercontrol/api` en producción
  (proxificado por nginx).
- **`frontend/src/pages/Nearby.jsx`**: usa `has_email`/`has_whatsapp` para
  mostrar los botones de contacto y `whatsapp_url`/`mailto_url` (de
  `contact-message`) para abrirlos — ya no construye los links ni recibe
  datos de contacto crudos de otros usuarios.
- **`frontend/src/pages/Dashboard.jsx`**: landing nueva arriba del resumen
  ("Controlá tus figuritas del Mundial 2026", bullets de pegadas/faltantes/
  repetidas y usuarios cerca, botón "Empezar" → `/buscar`).
- **`DEPLOY.md`**: reescrito con ejemplo real de nginx para
  `www.skillgames.com.ar` (bloque `/stickercontrol/api/` con `proxy_pass`
  y barra final, bloque `/stickercontrol/` con `alias` + `try_files` para
  el SPA fallback), systemd del backend, ubicación de
  `backend/stickercontrol.db` y backup diario con `sqlite3 .backup` + cron.
- Detalle completo y resultados de pruebas en
  [`DEPLOY_SKILLGAMES_REPORT.md`](./DEPLOY_SKILLGAMES_REPORT.md).

### Fase 0.6.1 — Auditoría forense de Usuarios cerca

Auditoría de privacidad sobre `/api/nearby` y
`/api/nearby/{user_id}/contact-message` con una base SQLite temporal y 9
usuarios (sin modificar código). Encontró el bug B1 (corregido en
Fase 0.6.2) y los riesgos R1-R4 (R2 también abordado en Fase 0.6.2 al
unificar el `404`). Detalle completo en
[`NEARBY_FORENSIC_TEST.md`](./NEARBY_FORENSIC_TEST.md).

### Fase 0.6 — Usuarios cerca (MVP de intercambio sin chat)

Nueva decisión de producto: la app se usará intensamente solo durante
pocos días/semanas (el Mundial), así que **no se implementa chat interno,
solicitudes de intercambio ni mensajería dentro de la app** (sin tablas
`messages`, sin notificaciones, sin moderación, sin WebSockets, sin
Firebase). En cambio se agregó una función mínima de "Usuarios cerca":

- `users` ahora tiene columnas de perfil público (todas opcionales,
  `is_public` default `false`): `display_name`, `city`, `latitude`,
  `longitude`, `contact_email`, `contact_whatsapp`. Migración liviana sin
  Alembic: `database.py::_ensure_user_profile_columns()` hace
  `ALTER TABLE users ADD COLUMN ...` si faltan, basado en
  `PRAGMA table_info(users)`.
- `app/geo.py`: `haversine_km()` (distancia aproximada) y `round_coord()`
  (redondea lat/lon a 2 decimales, ~1.1 km, antes de guardar — no se
  persiste ubicación exacta).
- `GET`/`PATCH /api/profile` (`routes/profile.py`): leer/editar el propio
  perfil. `PATCH` redondea coordenadas con `round_coord()`.
- `GET /api/nearby` (`routes/nearby.py`): cruza mis faltantes/repetidas
  (`crud.get_missing_and_duplicate_codes`, reutiliza `status.py`) contra las
  de cada usuario público, devuelve `distance_km`, listas de coincidencias y
  `match_count`. Ordenado por `match_count` desc, luego `distance_km` asc.
- `GET /api/nearby/{user_id}/contact-message`: genera el texto de contacto
  listo para copiar/WhatsApp/email.
- Frontend: nueva página `/cerca` (`pages/Nearby.jsx`) con formulario de
  perfil (incluye botón "Usar mi ubicación" vía `navigator.geolocation`) y
  tarjetas de coleccionistas cercanos con botones Copiar mensaje / WhatsApp
  (`wa.me`) / Email (`mailto:`). Agregada a `Layout.jsx` (nav de 7 items) y
  `App.jsx`.
- Detalle completo de alcance, privacidad y limitaciones en
  [`NEARBY_USERS_MVP.md`](./NEARBY_USERS_MVP.md).

### Fase 0.5 — Catálogo real de figuritas (nombres genéricos)

`master_stickers` ya tiene el catálogo **real** del álbum Mundial 2026 (980
figuritas: 48 selecciones x 20 + 19 especiales FIFA + 1 logo/portada),
importado desde `docs/StickerAlbumWC2026.xlsm` (hoja "Stickers") con
`scripts/import_master_stickers_from_xlsm.py`. Ver
[`IMPORT_MASTER_STICKERS_REPORT.md`](./IMPORT_MASTER_STICKERS_REPORT.md).

- **Cambio de criterio explícito del usuario**: no se importan nombres de
  jugadores reales todavía, porque hay varias listas/catálogos que no
  coinciden y no se quiere depender de ninguno hasta confirmar la fuente
  oficial. `player_name_or_detail` es genérico, derivado del código:
  `MEX1 -> "Mexico 1"`, `ARG10 -> "Argentina 10"`, `FWC1 -> "Especial FIFA 1"`.
  Esto se podrá enriquecer en una fase futura sin cambiar el esquema.
- **`country_name`** se toma literal de la columna "Country" de la hoja
  (en inglés, ej. "Mexico", "Czech Republic", "South Korea"), no se
  tradujo/acentuó.
- **Especiales FIFA (`FWC1`-`FWC19`)**: `country_code="FWC"`,
  `country_name="FIFA World Cup 2026"`, `type="special"`, `group=""` (vacío
  en el CSV -> `None` en la base). Se deja `group` vacío —no `"FWC"`—
  para preservar el comportamiento ya existente de `/api/reports/album`,
  que agrupa estas figuritas en la sección `special` (no como un "Grupo
  FWC" más). No se modificó `reports.py` ni el frontend para esto.
- **`seed_db.py`** ahora hace upsert por `code` **y además elimina** de
  `master_stickers` cualquier código que ya no esté en el CSV — necesario
  para que el dataset de prueba anterior (`FWC1`-`FWC5`, 85 filas) no quede
  como basura junto al catálogo real.
- **Código `00` (logo/portada del álbum)**: confirmado por revisión manual
  que NO es basura — es el sticker inicial/logo oficial del álbum. Se
  importa como `country_code="FWC"`, `country_name="FIFA World Cup 2026"`,
  `number=0`, `player_name_or_detail="Logo Oficial Mundial 2026"`,
  `type="logo"`, `group=""` (mismo criterio que los especiales FIFA, queda
  en la sección `special` de `/api/reports/album`).

### Decisiones de diseño

- **Usuario único local**: `init_db()` crea automáticamente un usuario
  `id=1` (`local@stickercontrol.local`, "Coleccionista Local") al arrancar
  el backend. `app/auth.py` define `get_current_user_id()` que devuelve
  `1` de forma fija. Todas las rutas de colección/reportes dependen de esa
  función, así que en Fase 1 se puede reemplazar por la lógica real de
  sesión/OAuth **sin tocar las rutas**.

- **`master_stickers` se crea vacía**: el esquema está listo, la tabla no
  trae datos precargados al crear la base. `backend/seed_db.py` importa un
  CSV (`data/stickers_master.csv`) haciendo upsert por `code`. El CSV
  actual es el **catálogo real** del álbum (980 figuritas, ver Fase 0.5
  arriba), con `player_name_or_detail` genérico. La idea es que en el
  futuro ese mismo CSV se enriquezca con nombres de jugadores reales (una
  vez confirmada la fuente oficial) y se vuelva a correr `seed_db.py` — el
  esquema no cambia.

- **`user_stickers` no se pre-llena**: si no existe una fila para un
  sticker+usuario, se asume `quantity=0, is_pasted=false` (es decir,
  FALTANTE). Las filas se crean (upsert) recién cuando el usuario hace la
  primera acción sobre esa figurita (pegar, sumar, marcar nota, etc.).

- **Intercambios (`/api/trades`)**: solo existe `GET /api/trades/status`
  devolviendo `{"implemented": false, "phase": "futura - intercambios"}`.
  Sin lógica todavía — el módulo queda preparado para una fase futura.

- **Assets de países/banderas**: `data/countries.json` y
  `frontend/public/flags/*` son una **copia** (no referencia) de
  `../data/countries.json` y `../frontend/public/flags/` del proyecto
  padre, generada por `scripts/sync_country_assets.py`. Si el proyecto
  padre actualiza esos archivos, hay que volver a correr el script.

### Reglas de estado (`backend/app/status.py`)

| quantity | is_pasted | status                  | repetidas         |
|----------|-----------|-------------------------|-------------------|
| 0        | false     | `FALTANTE`              | 0                 |
| >=1      | false     | `DISPONIBLE_PARA_PEGAR` | `quantity - 1`    |
| 0        | true      | `PEGADA_SIN_REPETIDA`   | 0                 |
| >=1      | true      | `PEGADA_CON_REPETIDA`   | `quantity`        |

### Mapeo de colores (frontend)

- `FALTANTE` → rojo (`bg-faltante` / `#ef4444`)
- `DISPONIBLE_PARA_PEGAR` → azul (`bg-disponible` / `#3b82f6`)
- `PEGADA_SIN_REPETIDA` → verde (`bg-pegada` / `#22c55e`)
- `PEGADA_CON_REPETIDA` → amarillo (`bg-repetida` / `#eab308`)

Definidos en `frontend/tailwind.config.js` y usados en
`StatusBadge.jsx`/`Album.jsx`.

## Verificación realizada

- Backend: venv creado, dependencias instaladas, `seed_db.py` carga las 980
  filas del catálogo real (1 insertada -código `00`-, 979 actualizadas, 0
  eliminadas), `uvicorn` corre en `:8000`. Probados:
  `/api/stickers/search?q=MEX1` (11 resultados, match por substring),
  `/api/stickers/search?q=ARG10` (1 resultado), `/api/stickers/search?q=00`
  (1 resultado, `type="logo"`), `/api/reports/album`
  (12 grupos A-L con 4 países cada uno + sección `special` con código `00`
  y FWC1-FWC19), ciclo `paste`/`increment`/`notes`, `/api/reports/missing`,
  `/api/reports/duplicates`, `/api/trades/status` (Fase 0).
- Frontend: `npm install` + `npm run dev` en `:5173`, proxy `/api` hacia
  `:8000` funcionando, todas las páginas (Dashboard, Buscar, Álbum,
  Faltantes, Repetidas, Intercambios) y componentes compilan sin errores,
  banderas servidas desde `/flags/*` (Fase 0; no se volvió a probar el
  frontend en Fase 0.5 porque no se modificó).
- **Fase 0.6 (Usuarios cerca)**: probado con una base SQLite temporal y dos
  usuarios (uno "yo" y un vecino público en Buenos Aires con figuritas que
  cruzan): `_ensure_user_profile_columns()` agrega las columnas nuevas sin
  romper la base existente, `PATCH /api/profile` redondea coordenadas a 2
  decimales (`-34.123456 -> -34.12`), `GET /api/nearby` devuelve
  `match_count`, `distance_km` (haversine, ~1.8 km para el caso de prueba) y
  las listas de coincidencias correctas, `GET /api/nearby/{id}/contact-message`
  genera el texto esperado. Frontend: `uvicorn :8000` + `npm run dev :5173`
  corriendo juntos, `/cerca` responde 200 y el proxy `/api/profile` /
  `/api/nearby` funciona contra la base real (`is_public=false` por
  defecto, `/api/nearby` devuelve `{"users": []}` hasta que alguien active
  su perfil público).
- **Fase 0.6.2 (deploy SkillGames)**: `npm run build` genera `dist/` con
  rutas `/stickercontrol/assets/...`; `npm run preview` confirma `200` en
  `/stickercontrol/`, `/stickercontrol/cerca` y `/stickercontrol/faltantes`
  (incluye SPA fallback). `npm run dev` confirma `base="/"`,
  `basename=""` y proxy `/api/nearby` funcionando en `:5174`. Backend
  arranca y expone los schemas actualizados (`NearbyUser.has_email/
  has_whatsapp`, `ContactMessageResponse.whatsapp_url/mailto_url`).
  Verificación de privacidad con base SQLite temporal de 3 usuarios:
  `contact-message` de un usuario privado y de uno inexistente devuelven
  `404`; de un usuario público devuelve `200` con `whatsapp_url`/
  `mailto_url` correctamente codificados. Detalle en
  [`DEPLOY_SKILLGAMES_REPORT.md`](./DEPLOY_SKILLGAMES_REPORT.md).

## Próximas fases

Ver [`TODO.md`](./TODO.md).
