# Auditoría — Login con Google / Multiusuario (Fase 2)

> **Documento de solo lectura / planificación.** No se modificó código,
> esquema de base de datos, dependencias ni configuración para esta
> auditoría. Cubre los 9 puntos solicitados + secciones del entregable.
> Cierra con una recomendación A/B/C.

---

## 1. Diagnóstico del estado actual

StickerControl 2026 está en **Fase 0.6.2** (`PROJECT_STATE.md`): desplegada
en `https://skillgames.com.ar/stickercontrol/`, single-user implícito
(`id=1`), sin login, sin OAuth, sin chat.

Lo más relevante para Fase 2: **el código ya fue diseñado explícitamente
para esta transición**. Tres evidencias directas:

- `backend/app/auth.py` (texto completo actual):

  ```python
  """
  Autenticacion - placeholder de Fase 0.

  En Fase 0 la app es de un solo usuario local (id=1, creado por
  database.init_db()). Todas las rutas dependen de get_current_user_id() en
  lugar de leer el usuario de una sesion/token, para que en Fase 1 (login con
  Google + multiples usuarios) solo haga falta reemplazar esta funcion por una
  que decodifique la sesion/JWT real - las rutas no cambian.
  """

  DEFAULT_USER_ID = 1

  def get_current_user_id() -> int:
      return DEFAULT_USER_ID
  ```

- **Todos** los routers (`stickers`, `collection`, `profile`, `nearby`,
  `reports`) ya declaran `user_id: int = Depends(get_current_user_id)` y
  filtran/escriben por `user_id`. Ninguno usa `1` hardcodeado directamente.
- `TODO.md` ya tiene una sección "Fase 1 — Login Google + multi-usuario" con
  los mismos puntos que pide esta auditoría (reemplazar
  `get_current_user_id()`, migrar la colección de `id=1`, sesiones,
  `GOOGLE_CLIENT_ID`/`SECRET`).

Conclusión: **el "core" (colección, álbum, faltantes, repetidas, perfil,
cerca) no necesita cambios de lógica**. El trabajo de Fase 2 es
mayormente: (a) un módulo de autenticación nuevo, (b) una función de
sesión que reemplace `get_current_user_id()`, (c) UI de login en el
frontend, y (d) una estrategia de migración para los datos de `id=1`.

---

## 2. Modelo actual de datos

El pedido menciona 6 "tablas": `users`, `user_stickers`, `profiles`,
`nearby`, `collection`, `reports`. En la base real (`backend/app/models.py`)
solo existen **3 tablas**; el resto son *features* calculadas sobre esas
3 tablas, sin tabla propia:

| Concepto pedido | Tabla real | Notas |
|---|---|---|
| `users` | `users` | Existe. PK `id`, `email` (unique), `name`, `avatar`, `created_at`. |
| `user_stickers` | `user_stickers` | Existe. FK `user_id` → `users.id`, FK `sticker_id` → `master_stickers.id`, `UNIQUE(user_id, sticker_id)`. |
| `profiles` | **columnas dentro de `users`** | `display_name`, `city`, `latitude`, `longitude`, `contact_email`, `contact_whatsapp`, `is_public` (agregadas en Fase 0.6 vía `_ensure_user_profile_columns`). No es tabla aparte. |
| `nearby` | **sin tabla** | `GET /api/nearby` es una consulta en memoria: cruza `users.is_public=true` con `user_stickers` de cada usuario (vía `crud.get_missing_and_duplicate_codes`). No persiste nada. |
| `collection` | **sin tabla** | "Colección" = `user_stickers` filtrado por `user_id`, combinado con `master_stickers` (catálogo, ~980 filas, **no se toca**). |
| `reports` | **sin tabla** | `/api/reports/album`, `/missing`, `/duplicates` son agregaciones en memoria sobre `master_stickers` + `user_stickers` del `user_id` actual. |

Esquema completo actual:

```python
class User(Base):
    __tablename__ = "users"
    id, email (unique, index), name, avatar, created_at
    # perfil público (Fase 0.6, todo opcional / is_public default False):
    display_name, city, latitude, longitude, contact_email,
    contact_whatsapp, is_public
    stickers: list[UserSticker]

class MasterSticker(Base):       # NO TOCAR (980 filas, catálogo real)
    __tablename__ = "master_stickers"
    id, code (unique), group, country_code, country_name, number,
    player_name_or_detail, type

class UserSticker(Base):
    __tablename__ = "user_stickers"
    UNIQUE(user_id, sticker_id)
    id, user_id (FK users), sticker_id (FK master_stickers),
    quantity, is_pasted, notes, updated_at
```

`backend/stickercontrol.db` (SQLite, **116 KB** hoy) contiene estas 3
tablas con datos reales: el catálogo de 980 figuritas y la colección del
usuario `id=1`.

---

## 3. Qué partes ya están preparadas para multiusuario

- **`user_stickers`**: ya tiene `user_id` como FK + `UNIQUE(user_id,
  sticker_id)`. Soporta N usuarios sin ningún cambio de esquema — es
  exactamente la tabla que se necesita para "cada usuario tiene su propia
  colección".
- **Todos los endpoints de negocio** (`/api/collection/*`,
  `/api/reports/*`, `/api/stickers/search`, `/api/profile`,
  `/api/nearby*`) ya reciben `user_id` vía `Depends(get_current_user_id)` y
  ya filtran/escriben por ese `user_id`. **No requieren cambios de lógica.**
- **`users` ya tiene `email` único** — la clave natural para emparejar con
  la identidad de Google.
- **Perfil público + "Usuarios cerca" (Fase 0.6)** ya es una feature
  multiusuario real: `is_public`, `display_name`, geolocalización
  redondeada, `match_count` entre pares de usuarios — todo ya opera sobre
  múltiples filas de `users`. Hoy solo hay una fila (`id=1`) que nunca tiene
  `is_public=true` por defecto, pero el código no asume `id=1` en ningún
  cálculo de `nearby` (usa `user_id` del dependency).
- **Patrón de migración liviana sin Alembic** ya existe y funciona:
  `database.py::_ensure_user_profile_columns()` hace `ALTER TABLE users ADD
  COLUMN ...` idempotente basado en `PRAGMA table_info`. Se puede reutilizar
  el mismo patrón para agregar columnas de Google (ej. `google_id`).
- **CORS ya tiene `allow_credentials=True`** (`main.py`) — precondición para
  que el navegador envíe cookies de sesión en requests a `/api/*`.
- **Frontend y backend están en el mismo origen en producción**
  (`/stickercontrol/` y `/stickercontrol/api/` bajo `skillgames.com.ar`),
  lo que simplifica mucho cookies de sesión (sin problemas de cross-site).

---

## 4. Qué partes siguen usando usuario fijo/default

Solo dos puntos concretos en todo el código:

1. **`backend/app/auth.py`** — `get_current_user_id()` devuelve `1` siempre.
   Este es **el único lugar que hay que reemplazar** para que las rutas
   dependan del usuario real.

2. **`backend/app/database.py::init_db()`** — en cada arranque, si no
   existe el usuario `id=1`, lo crea:
   ```python
   default_user = models.User(
       id=1, email="local@stickercontrol.local",
       name="Coleccionista Local", avatar=None,
   )
   ```
   Esto seguirá ejecutándose tal cual salvo que se decida lo contrario (ver
   §12) — no rompe nada porque solo actúa si `id=1` no existe.

3. **Frontend**: no hay ningún concepto de usuario/sesión.
   `frontend/src/api/client.js` no envía tokens, headers de auth ni
   `credentials`. No hay `AuthContext`, no hay página de login, no hay
   guard de rutas en `App.jsx`/`main.jsx`. Todo el frontend asume
   implícitamente "el usuario actual" porque el backend siempre responde
   como `id=1`.

No hay ningún otro `user_id = 1`, `WHERE id = 1` ni constante similar fuera
de estos dos archivos (`crud.py` y los `routes/*.py` reciben `user_id` por
parámetro, no lo hardcodean).

---

## 5. Qué endpoints deben pasar a depender del usuario autenticado

**Respuesta corta: todos los que ya dependen de `get_current_user_id`, sin
tocar su código** — porque reemplazar esa función basta:

| Router | Endpoints | Cambio de código necesario |
|---|---|---|
| `routes/stickers.py` | `GET /api/stickers/search` | Ninguno (ya usa `Depends(get_current_user_id)`) |
| `routes/collection.py` | `POST /api/collection/{id}/paste\|unpaste\|increment\|decrement\|mark-missing`, `PATCH /api/collection/{id}/notes` | Ninguno |
| `routes/profile.py` | `GET`/`PATCH /api/profile` | Ninguno |
| `routes/nearby.py` | `GET /api/nearby`, `GET /api/nearby/{id}/contact-message` | Ninguno |
| `routes/reports.py` | `GET /api/reports/album\|missing\|duplicates` | Ninguno |
| `routes/trades.py` | `GET /api/trades/status` | Ninguno (sin lógica todavía, no usa auth) |

Lo único **nuevo** es un router de autenticación que hoy no existe:

| Router nuevo | Endpoints propuestos |
|---|---|
| `routes/auth.py` (nuevo) | `POST /api/auth/google` (login), `GET /api/auth/me`, `POST /api/auth/logout` |

Y `get_current_user_id()` deja de ser una constante y pasa a:
1. Leer la sesión (cookie firmada).
2. Si no hay sesión válida → `401 Unauthorized`.
3. Si hay sesión válida → devolver el `user_id` real.

Las rutas existentes ya manejan `Depends(...)`, así que un `401` ahí
simplemente hace que FastAPI devuelva 401 antes de ejecutar el handler —
sin tocar ningún `routes/*.py`.

---

## 6. Arquitectura recomendada (flujo de login propuesto)

**Patrón: Google Identity Services (GIS) "Sign In with Google" en el
frontend + verificación de ID token en el backend + sesión por cookie
firmada.** Se descarta el flujo "authorization code" clásico (no requiere
`GOOGLE_CLIENT_SECRET`, menos superficie, menos dependencias).

```
┌─────────────┐                                  ┌──────────────┐
│  Navegador  │                                  │   Backend     │
│  (React)    │                                  │  (FastAPI)    │
└─────┬───────┘                                  └──────┬────────┘
      │ 1. Botón "Sign in with Google" (script GIS)      │
      │    devuelve un ID token (JWT) firmado por Google │
      │                                                   │
      │ 2. POST /api/auth/google { credential: <jwt> }   │
      ├──────────────────────────────────────────────────▶
      │                                                   │ 3. Verifica firma/aud/iss
      │                                                   │    con google-auth
      │                                                   │ 4. Busca/crea User por
      │                                                   │    google_id / email
      │                                                   │ 5. Crea sesión (cookie
      │                                                   │    firmada, httponly,
      │                                                   │    secure, samesite=lax)
      │ 6. 200 OK + Set-Cookie + datos de usuario        │
      ◀──────────────────────────────────────────────────┤
      │                                                   │
      │ 7. Requests normales a /api/* incluyen la cookie │
      │    (credentials: "include")                      │
      ├──────────────────────────────────────────────────▶
      │                                                   │ get_current_user_id()
      │                                                   │ lee la cookie -> user_id
```

Componentes:

- **Frontend**: `<script src="https://accounts.google.com/gsi/client">` en
  `index.html` (sin nueva dependencia npm) + botón de Google que entrega un
  `credential` (JWT). `AuthContext`/`useAuth` guarda el usuario actual
  (via `GET /api/auth/me` al cargar la app) y un `ProtectedRoute`/redirect
  a `/login` si no hay sesión.
- **Backend**: `google-auth` para `verify_oauth2_token(credential,
  audience=GOOGLE_CLIENT_ID)` → obtiene `email`, `name`, `picture`, `sub`
  (= `google_id`). Sesión via `starlette.middleware.sessions.SessionMiddleware`
  (cookie firmada con `itsdangerous`, sin estado en servidor — no requiere
  tabla `sessions`).
- **`get_current_user_id()`** pasa a leer `request.session["user_id"]`.

Por qué este patrón y no otro:
- Sin `GOOGLE_CLIENT_SECRET` → menos secretos que proteger en el VPS.
- Sin tabla de sesiones ni Redis → coherente con "app de uso intensivo
  durante pocas semanas" (mismo criterio que `NEARBY_USERS_MVP.md` para
  descartar infraestructura pesada).
- Cookie de sesión + `allow_credentials=True` (ya configurado) + mismo
  origen en producción → no hay problemas de CORS/cookies cross-site.

---

## 7. Cambios necesarios — Backend

| Archivo | Cambio |
|---|---|
| `backend/app/auth.py` | Reemplazar `get_current_user_id()` por una dependencia que lee `request.session["user_id"]`; `401` si falta. Mantener el nombre/firma para no tocar `routes/*.py`. |
| `backend/app/main.py` | Agregar `SessionMiddleware` (secret desde env); registrar nuevo router `auth`; revisar `CORS_ORIGINS` en prod. |
| `backend/app/models.py` | Agregar columna `google_id: str \| None` (nullable, unique/index) a `User`. `email` ya es unique — sirve como fallback de búsqueda. |
| `backend/app/database.py` | Extender el patrón de `_ensure_user_profile_columns()` para `google_id` (mismo `ALTER TABLE ... ADD COLUMN` idempotente). Revisar si `init_db()` debe seguir creando `id=1` automáticamente (ver §12). |
| `backend/app/schemas.py` | Nuevos schemas: `GoogleLoginRequest` (`credential: str`), `UserOut` (id, email, name, avatar, picture). |
| `backend/app/routes/auth.py` (nuevo) | `POST /api/auth/google`, `GET /api/auth/me`, `POST /api/auth/logout`. |
| `backend/requirements.txt` | Agregar `google-auth` (verificación de ID token) e `itsdangerous` (firma de cookies de sesión, usado por `SessionMiddleware`). |
| `backend/.env.example` | Agregar variables nuevas (ver §9), sin tocar las existentes. |

No se modifica: `crud.py`, `status.py`, `geo.py`, `countries.py`,
`routes/stickers.py`, `routes/collection.py`, `routes/profile.py`,
`routes/nearby.py`, `routes/reports.py`, `routes/trades.py`,
`seed_db.py`, `master_stickers` ni los códigos de figuritas.

---

## 8. Cambios necesarios — Frontend

| Archivo | Cambio |
|---|---|
| `frontend/index.html` | Agregar `<script src="https://accounts.google.com/gsi/client" async defer>`. |
| `frontend/src/api/client.js` | Agregar `credentials: "include"` a las opciones de `fetch` en `request()`; agregar `loginWithGoogle(credential)`, `getMe()`, `logout()`. |
| `frontend/src/context/AuthContext.jsx` (nuevo) | Provider que llama `GET /api/auth/me` al montar, expone `{ user, loading, login, logout }`. |
| `frontend/src/pages/Login.jsx` (nuevo) | Pantalla de login con el botón de Google (renderizado por el script GIS), sin tocar el resto del diseño/paleta. |
| `frontend/src/App.jsx` | Agregar ruta `/login`; envolver las rutas existentes en un guard que redirige a `/login` si `user == null`. **No cambia ninguna ruta existente.** |
| `frontend/src/components/Layout.jsx` | Mostrar avatar/nombre del usuario + botón "Salir" (logout) en el header/nav existente — sin tocar la navegación inferior de 7 items ni el diseño responsive recién ajustado. |
| `frontend/.env` / `vite.config.js` | Variable `VITE_GOOGLE_CLIENT_ID` (pública, build-time — el client ID de Google no es secreto). |
| `frontend/package.json` | Sin nuevas dependencias npm si se usa el script GIS directo (recomendado, evita bundlear librerías de auth). |

No se modifica: `Dashboard.jsx`, `Album.jsx`, `Missing.jsx`,
`Duplicates.jsx`, `Search.jsx`, `Nearby.jsx`, `Trades.jsx`,
`StickerCard.jsx`, `StickerDetailModal.jsx`, `ProgressRing.jsx`,
`tailwind.config.js`, ni la estructura responsive de
`RESPONSIVE_STRUCTURE_FIX_REPORT.md`.

---

## 9. Configuración externa necesaria (Google OAuth)

En [Google Cloud Console](https://console.cloud.google.com/) (proyecto
nuevo o existente):

1. **OAuth consent screen**: tipo "External", nombre de la app
   ("StickerControl 2026"), scopes mínimos (`openid`, `email`, `profile` —
   son los que GIS pide por defecto, no requieren configuración extra).
2. **Credenciales → OAuth client ID → tipo "Web application"**:
   - **Authorized JavaScript origins**:
     - `https://skillgames.com.ar`
     - `http://localhost:5173` y `http://localhost:5174` (dev/preview)
   - **Authorized redirect URIs**: con el flujo de ID token (GIS) no hace
     falta un redirect URI de servidor; si en el futuro se migra a
     "authorization code flow" sí se necesitaría
     `https://skillgames.com.ar/stickercontrol/api/auth/callback/google`.
3. Resultado: un **Client ID** (público) — no se genera/usa Client Secret
   con este flujo.

Variables de entorno resultantes (ver §10): solo `GOOGLE_CLIENT_ID` (uno
solo, usado tanto por frontend como backend — backend lo usa como
`audience` al verificar el token).

---

## 10. Variables de entorno necesarias

`backend/.env.example` actual (sin cambios a lo existente, solo se agrega
al final):

```diff
 # Fase 0: sin variables de OAuth. Copiar este archivo a .env y ajustar si hace falta.

 # URL de la base de datos SQLite (ruta relativa a backend/)
 DATABASE_URL=sqlite:///./stickercontrol.db

 # Origenes permitidos para CORS (separados por coma)
 CORS_ORIGINS=http://localhost:5173
+
+# Fase 2: login con Google
+# Client ID de Google Cloud Console (OAuth consent screen). Mismo valor
+# que VITE_GOOGLE_CLIENT_ID en el frontend.
+GOOGLE_CLIENT_ID=
+
+# Secreto para firmar la cookie de sesion (SessionMiddleware). Generar con
+# `python -c "import secrets; print(secrets.token_hex(32))"`.
+SESSION_SECRET_KEY=
+
+# Email de la cuenta de Google que va a "reclamar" la coleccion actual
+# (usuario id=1, "Coleccionista Local") en su primer login. Ver migracion.
+LEGACY_OWNER_EMAIL=
+
+# Cookie de sesion con flag Secure (requiere HTTPS). true en produccion,
+# false en desarrollo local (http://localhost).
+SESSION_COOKIE_SECURE=true
```

`frontend/.env` (nuevo, no existe hoy un `.env` de frontend):

```
VITE_GOOGLE_CLIENT_ID=<mismo Client ID que GOOGLE_CLIENT_ID>
```

**No se necesita `GOOGLE_CLIENT_SECRET`** con el flujo recomendado (ID
token de GIS verificado en backend).

---

## 11. Riesgos de migración de la base de datos actual

- **Archivo real**: `backend/stickercontrol.db`, **116 KB**, contiene
  `master_stickers` (980 filas, catálogo real) + `users` (1 fila, `id=1`) +
  `user_stickers` (colección actual). **Está fuera del control de versiones
  y es el único lugar donde vive la colección actual** — cualquier cambio
  de esquema debe ser additive y reversible.

- **Cambio de esquema propuesto**: una sola columna nueva, nullable,
  `users.google_id` — vía `ALTER TABLE users ADD COLUMN google_id VARCHAR`,
  siguiendo exactamente el patrón ya probado de
  `_ensure_user_profile_columns()` (Fase 0.6, ya corrió sobre esta misma
  base sin problemas). Riesgo: **bajo** — es el mismo mecanismo que ya se
  usó para agregar `display_name`, `city`, `latitude`, etc.

- **No se toca**: `master_stickers` (esquema ni datos), `user_stickers`
  (esquema), códigos de figuritas, ningún dato existente de `user_id=1`.

- **Riesgo real no es de esquema, es de *identidad***: hoy "la colección"
  =`user_id=1`. Si el primer login de Google crea un usuario nuevo
  (`id=2`), esa cuenta arranca con colección **vacía** y el dueño verá "se
  borró todo" aunque los datos de `id=1` sigan intactos en la base. Este es
  el riesgo principal de Fase 2 y se resuelve con la estrategia de §12, no
  con cambios de esquema.

- **Backups**: antes de aplicar el `ALTER TABLE` en el VPS, copiar
  `stickercontrol.db` (`sqlite3 stickercontrol.db ".backup
  stickercontrol.db.bak-fase2"`), siguiendo el mismo procedimiento descrito
  en `DEPLOY.md` para los backups diarios. Probar todo el flujo primero
  contra una **copia** de la base de producción en local, no contra la
  base real.

- **SQLite + concurrencia**: sin cambios — sigue siendo `check_same_thread:
  False` con un solo proceso `uvicorn`. Login y reclamo de `id=1` son
  operaciones puntuales (no agregan carga sostenida).

---

## 12. Estrategia para preservar los datos actuales (usuario actual / demo)

**Recomendación: "reclamo" (claim) de `id=1` por el owner, en el primer
login real.**

1. Se define `LEGACY_OWNER_EMAIL` (env var, ej. el email de Google del
   dueño actual de la colección).
2. En `POST /api/auth/google`, tras verificar el token de Google:
   - Si el `email` del token Google == `LEGACY_OWNER_EMAIL` **y** el
     usuario `id=1` todavía tiene `email="local@stickercontrol.local"`
     (es decir, todavía no fue "reclamado"):
     → **actualizar la fila `id=1` in-place**: `email`, `name`, `avatar` y
     el nuevo `google_id` pasan a ser los reales del owner. Como
     `user_stickers.user_id=1` no cambia, **toda la colección actual queda
     intacta y automáticamente asociada a la cuenta de Google del owner**.
   - Para cualquier otro email de Google (otros usuarios): buscar por
     `google_id`/`email`; si no existe, **crear un usuario nuevo** (`id=2,
     3, ...`) con colección vacía — exactamente el comportamiento esperado
     de "multiusuario real".
3. Una vez reclamado `id=1`, esa rama de código no vuelve a ejecutarse
   (`email` ya no es `local@stickercontrol.local`) — es un "one-time claim",
   no una regla permanente.

Por qué esta estrategia y no otras:
- No requiere script de migración manual aparte ni tocar
  `user_stickers`/`master_stickers`.
- Es **reversible**: si algo falla, `id=1` sigue teniendo
  `email="local@stickercontrol.local"` y los datos no se movieron.
- Cubre exactamente la restricción "no perder `stickercontrol.db`" y "cómo
  preservar los datos cargados actualmente": los datos no se mueven, se
  **re-etiqueta el dueño** de la fila que ya los tiene.

Sobre `init_db()` creando `id=1` automáticamente: se puede dejar tal cual
— solo crea esa fila si **no existe**, así que después del primer reclamo
(`id=1` ya existe con el email real) no vuelve a crear un "Coleccionista
Local" duplicado. Si se prefiere, en una fase posterior se puede condicionar
esa creación a que no exista ningún usuario en la tabla, pero no es
necesario para Fase 2.

---

## 13. Riesgos generales

1. **Identidad/colección "perdida" si no se implementa §12** — el riesgo
   más alto, ya cubierto arriba.
2. **Verificación de token mal configurada**: si `verify_oauth2_token` no
   valida `audience` (=`GOOGLE_CLIENT_ID`) e `issuer`, un token de Google
   válido para *otra* app podría aceptarse. Mitigación: usar siempre la
   función oficial de `google-auth` con `audience` explícito, nunca decodificar
   el JWT "a mano".
3. **Cookies de sesión + nginx**: la cookie debe poder viajar en
   `/stickercontrol/api/*`. Como frontend y backend están en el mismo
   origen (`skillgames.com.ar`) en producción, no hay problema de
   `SameSite`/CORS — pero hay que verificar el `CORS_ORIGINS` real del
   `.env` en el VPS (no versionado) incluya el origen de producción si
   `allow_credentials=True` (Starlette rechaza `*` con credentials).
4. **`SESSION_COOKIE_SECURE=true` requiere HTTPS** — ya hay HTTPS en
   producción (nginx, según `DEPLOY.md`), pero en desarrollo local
   (`http://localhost`) debe poder desactivarse vía env var, o el login no
   funcionará en `npm run dev`.
5. **"Usuarios cerca" con usuarios reales**: hasta ahora `is_public` nunca
   fue `true` en producción (single-user). Con login real, varios usuarios
   podrían activar `is_public` y aparecer entre sí — es el comportamiento
   *deseado* de la feature (`NEARBY_USERS_MVP.md`), pero conviene
   confirmarlo como aceptado para Fase 2 (no es un bug nuevo, es la feature
   funcionando con datos reales por primera vez).
6. **Bundle cacheado**: como en cambios previos, tras el deploy hay que
   confirmar que el navegador carga el JS/CSS nuevo (mismo punto que
   `ROOT_CAUSE_ANALYSIS_P1_FAILURE.md`).
7. **Sin Alembic**: el patrón `_ensure_*_columns()` es manual; agregar
   `google_id` correctamente implica actualizar también ese helper (o uno
   equivalente) — si se olvida, `ALTER TABLE` no corre y el login fallaría
   en producción aunque funcione en local con una base recién creada por
   `init_db()` (que sí incluiría la columna desde el `CREATE TABLE`).

---

## 14. Plan de implementación por fases

**Fase 2.0 — Preparación (bajo riesgo, no visible para el usuario)**
- Crear OAuth Client ID en Google Cloud Console (fuera del repo).
- Agregar `google-auth` e `itsdangerous` a `requirements.txt`.
- Agregar variables nuevas a `.env.example` (sin valores reales).
- Agregar columna `google_id` a `User` + extender el helper de migración
  liviana (`_ensure_user_profile_columns` o uno nuevo análogo).
- Backup de `stickercontrol.db` antes de tocar nada en el VPS.

**Fase 2.1 — Backend: autenticación**
- Nuevo `routes/auth.py` (`/api/auth/google`, `/api/auth/me`,
  `/api/auth/logout`).
- `SessionMiddleware` en `main.py`.
- Reemplazar `get_current_user_id()` (lectura de sesión + 401).
- Implementar el "claim" de `id=1` (§12).
- Probar contra una **copia local** de `stickercontrol.db` (no la de
  producción): login del owner reclama `id=1` y conserva su colección;
  login de otra cuenta crea `id=2` con colección vacía.

**Fase 2.2 — Frontend: login**
- Script GIS + `Login.jsx` + `AuthContext` + guard de rutas en `App.jsx`.
- `client.js`: `credentials: "include"`.
- `Layout.jsx`: avatar/nombre + "Salir", sin tocar nav inferior ni
  estructura responsive.
- Probar local (`npm run dev`) con Client ID autorizado para
  `localhost:5173`.

**Fase 2.3 — Deploy y migración de datos reales**
- Backup de `stickercontrol.db` en el VPS.
- Deploy backend (nuevas deps + `.env` real con `GOOGLE_CLIENT_ID`,
  `SESSION_SECRET_KEY`, `LEGACY_OWNER_EMAIL`) + frontend (`VITE_GOOGLE_CLIENT_ID`,
  `npm run build`).
- Primer login del owner → verificar que `id=1` se reclama y
  `/api/reports/album` sigue mostrando la colección preexistente.
- Segundo login (otra cuenta) → verificar colección vacía e independiente.
- Verificar `/cerca` con `is_public` entre cuentas reales.

**Fase 2.4 (opcional, futura, fuera de alcance de esta auditoría)**
- Expiración/renovación de sesión, logout en todos los dispositivos.
- Rate limiting en `/api/auth/google`.
- Posible export/backup de datos por usuario (relacionado con Fase 3 del
  `TODO.md`).

---

## 15. Recomendación final

**A) Implementar login completo con Google ahora.**

Motivos:
- El código fue **diseñado deliberadamente** para este momento
  (`auth.py`, `TODO.md` Fase 1) — no es una funcionalidad improvisada
  sobre una base que la resista mal.
- `user_stickers` ya soporta N usuarios sin cambios de esquema; el único
  cambio de esquema real es **una columna nullable** (`google_id`), con un
  patrón de migración ya usado y probado en esta misma base
  (`_ensure_user_profile_columns`).
- El riesgo más serio — "perder" la colección actual al pasar a
  multiusuario — tiene una solución concreta y de bajo riesgo (§12, claim
  de `id=1`), que no mueve datos, solo re-etiqueta el dueño de una fila.
- La opción B (password simple) no resuelve mejor el problema de
  "colección actual/demo" y agrega trabajo (hashing, recuperación de
  contraseña) que después habría que reemplazar igual por Google. La
  opción C (seguir single-user) no cumple el objetivo explícito ("cada
  usuario tenga su propia colección"), y la app ya está en producción con
  el Mundial en curso — cuanto más tiempo pase en single-user, más difícil
  será separar "datos del owner" de "datos de otros usuarios reales" si
  alguien más empieza a usarla contra `id=1` sin login.

Condición para avanzar: ejecutar Fase 2.1 contra una **copia** de
`stickercontrol.db` y validar el "claim" de `id=1` end-to-end antes de
tocar la base de producción (Fase 2.3).
