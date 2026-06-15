# StickerControl 2026

Aplicación web para reemplazar la planilla Excel/Google Sheets de control de
figuritas del álbum del Mundial 2026. Permite buscar figuritas, marcarlas
como pegadas/faltantes/repetidas, ver el álbum completo agrupado por grupo
(A-L), generar listas de faltantes/repetidas listas para compartir por
WhatsApp, y encontrar coleccionistas cerca para intercambiar.

> **Estado actual: Fase 0.6.2 (preparado para deploy bajo SkillGames, sin
> login).** No hay login ni usuarios múltiples todavía — la app corre con un
> único usuario implícito (`id=1`). El catálogo de figuritas (980) ya es el
> real del álbum Mundial 2026, pero con nombres **genéricos** (sin jugadores
> reales todavía — ver sección "Catálogo de figuritas"). Incluye una función
> mínima de "Usuarios cerca" para intercambio (sin chat interno) — ver
> [`NEARBY_USERS_MVP.md`](./NEARBY_USERS_MVP.md) y la auditoría de privacidad
> en [`NEARBY_FORENSIC_TEST.md`](./NEARBY_FORENSIC_TEST.md). El frontend está
> preparado para servirse bajo `/stickercontrol/` (build de producción) y la
> API bajo `/stickercontrol/api/` — ver [`DEPLOY.md`](./DEPLOY.md) y
> [`DEPLOY_SKILLGAMES_REPORT.md`](./DEPLOY_SKILLGAMES_REPORT.md). Ver
> [`PROJECT_STATE.md`](./PROJECT_STATE.md) y [`TODO.md`](./TODO.md) para el
> detalle de fases.

## Arquitectura

```
stickercontrol-2026/
  backend/    FastAPI + SQLAlchemy + SQLite
  frontend/   Vite + React + Tailwind CSS
  data/       countries.json, flags (copiados) y stickers_master.csv (catálogo real, nombres genéricos)
  scripts/    utilidades (sync de assets de países, importación del catálogo)
```

- **Backend**: FastAPI expone la API en `/api/...`, persistida en SQLite
  (`backend/stickercontrol.db`, se crea sola al arrancar).
- **Frontend**: Vite + React + Tailwind. En desarrollo usa `base: "/"` y un
  proxy de `/api` hacia el backend (puerto 8000); en producción
  (`npm run build`) usa `base: "/stickercontrol/"` y el cliente API apunta a
  `/stickercontrol/api` (servido por nginx, ver [`DEPLOY.md`](./DEPLOY.md)).
- **Datos de países/banderas**: copiados una sola vez desde el proyecto
  padre (`../data/countries.json` y `../frontend/public/flags/`) con
  `scripts/sync_country_assets.py`. Si esos datos cambian en el proyecto
  padre, correr el script de nuevo para actualizar la copia.

## Requisitos

- Python 3.10+ (en Windows, usar el launcher `py`)
- Node.js 18+ y npm

## Backend: cómo correrlo

```bash
cd backend
py -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Cargar el catálogo en master_stickers (crea la base si no existe)
py seed_db.py

# Levantar la API en http://localhost:8000
py -m uvicorn app.main:app --reload --port 8000
```

Copiá `backend/.env.example` a `backend/.env` si querés ajustar
`DATABASE_URL` o `CORS_ORIGINS` (los valores por defecto ya sirven para
desarrollo local).

Endpoints principales:

- `GET /api/stickers/search?q=&group=&country_code=&type=` — buscador
- `POST /api/collection/{id}/paste|unpaste|increment|decrement|mark-missing`
- `PATCH /api/collection/{id}/notes`
- `GET /api/reports/album` — álbum agrupado A-L + especiales (FWC)
- `GET /api/reports/missing` — faltantes + texto para WhatsApp
- `GET /api/reports/duplicates` — repetidas + texto para WhatsApp
- `GET /api/trades/status` — placeholder (Fase futura)
- `GET`/`PATCH /api/profile` — perfil público para "Usuarios cerca"
  (nombre, ciudad, ubicación aproximada, contacto, `is_public`)
- `GET /api/nearby` — coleccionistas cercanos con coincidencias de
  intercambio (`match_count`, `distance_km`, `has_email`/`has_whatsapp`;
  nunca expone el email/WhatsApp en texto plano)
- `GET /api/nearby/{user_id}/contact-message` — texto + `whatsapp_url`/
  `mailto_url` listos para usar; devuelve `404` si el usuario no existe o
  no es público

## Frontend: cómo correrlo

```bash
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5173`. El proxy de Vite redirige `/api/*` hacia
`http://localhost:8000`, así que el backend tiene que estar corriendo en
paralelo.

## Catálogo de figuritas

`data/stickers_master.csv` contiene el catálogo **real** del álbum Mundial
2026: 48 selecciones (12 grupos A-L x 4 países, 20 figuritas cada una) + 19
figuritas especiales FIFA (`FWC1`-`FWC19`) + 1 logo/portada (código `00`),
**980 filas en total**. Se generó
con `scripts/import_master_stickers_from_xlsm.py` a partir de
`../docs/StickerAlbumWC2026.xlsm` (hoja "Stickers"). Detalle de la
importación en [`IMPORT_MASTER_STICKERS_REPORT.md`](./IMPORT_MASTER_STICKERS_REPORT.md).

> **`player_name_or_detail` es genérico por ahora** (ej. `"Mexico 1"`,
> `"Argentina 10"`, `"Especial FIFA 1"`), derivado del código de figurita —
> **todavía no hay nombres de jugadores reales**, porque existen varios
> catálogos/listas que no coinciden entre sí y no se quiere depender de
> ninguno hasta confirmar la fuente oficial definitiva. Esto se podrá
> enriquecer en una fase futura sin cambiar el esquema (mismas columnas:
> `code,group,country_code,country_name,number,player_name_or_detail,type`).

La tabla `master_stickers` se crea **vacía** y se puebla con `py seed_db.py`,
que hace upsert por `code` y elimina cualquier código que ya no esté en el
CSV (para que la tabla refleje exactamente el catálogo del CSV).

## Reglas de estado

Ver detalle en [`PROJECT_STATE.md`](./PROJECT_STATE.md).

## Usuarios cerca (intercambio sin chat)

La página "Usuarios cerca" (`/cerca`) deja completar un perfil público
opcional (nombre, ciudad, ubicación aproximada, contacto) y muestra otros
coleccionistas públicos cercanos con sus coincidencias de intercambio
(qué le falta a cada uno). El contacto se hace por WhatsApp o email, fuera
de la app — **no hay chat interno ni mensajería**. Alcance, privacidad y
limitaciones completas en [`NEARBY_USERS_MVP.md`](./NEARBY_USERS_MVP.md).

## Próximos pasos

Ver [`TODO.md`](./TODO.md) para el roadmap (Fase 1: login Google +
multi-usuario, Fase 2: intercambios, Fase 3: export/backup + deploy). Guía
de deploy en [`DEPLOY.md`](./DEPLOY.md) y resumen de los cambios de la
Fase 0.6.2 en [`DEPLOY_SKILLGAMES_REPORT.md`](./DEPLOY_SKILLGAMES_REPORT.md).
