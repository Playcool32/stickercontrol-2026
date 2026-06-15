# Implementación: Login con Google multiusuario (Fase 2A)

Basado en `GOOGLE_LOGIN_MULTIUSER_AUDIT.md`. Decisión de producto: opción 2
(mini red de intercambio de figuritas) — esta fase **solo** cubre login,
sesión y aislamiento de colección por usuario. No se tocó chat, solicitudes
de intercambio ni nuevas funciones sociales.

Por instrucción explícita, **no se preservaron los datos de prueba del
`user_id=1`** (no era necesario "reclamar" ese id). El esquema se extendió de
forma aditiva y no destructiva.

## 0. Backup de base de datos

Antes de tocar nada se generó una copia de la base real:

```
backend/stickercontrol.db.bak-fase2a-20260615-134401
```

(`cp stickercontrol.db stickercontrol.db.bak-fase2a-$(date +%Y%m%d-%H%M%S)`,
ejecutado antes de aplicar la migración.)

## 1. Cambios en el backend

### `backend/requirements.txt`
Agregadas las dependencias nuevas:
- `google-auth==2.54.0` (valida el ID token de Google).
- `itsdangerous==2.2.0` (requerido por `SessionMiddleware` de Starlette).
- `requests==2.34.2` (requerido transitivamente por
  `google.auth.transport.requests`).

Todas instaladas en `backend/.venv` y verificadas.

### `backend/app/models.py`
`User` ahora tiene `google_id` (nullable, único, indexado):

```python
class User(Base):
    """Usuario autenticado con Google (Fase 2A). Cada usuario tiene su
    propia coleccion en user_stickers."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    # display_name, city, latitude, longitude, contact_email,
    # contact_whatsapp, is_public, stickers -> sin cambios
```

`MasterSticker` y `UserSticker` **no se modificaron** (master_stickers global
intacto, códigos sin cambios).

### `backend/app/database.py`
- `_ensure_user_profile_columns()` sin cambios.
- Nueva `_ensure_user_google_id_column()`: agrega `users.google_id` con
  `ALTER TABLE ADD COLUMN` si falta, y crea
  `CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)`.
  SQLite no permite agregar una constraint `UNIQUE` vía `ALTER TABLE`, por eso
  el índice único se crea aparte; los `NULL` no chocan entre sí en un índice
  único de SQLite, así que las filas existentes sin `google_id` no se ven
  afectadas.
- **Se eliminó** la creación automática del usuario `id=1`
  (`local@stickercontrol.local` / "Coleccionista Local") que hacía
  `init_db()` en la Fase 0. Esa fila sigue existiendo en la base real (no se
  borró, por seguridad), pero queda huérfana: ningún usuario de Google podrá
  "convertirse" en ella, y los usuarios nuevos arrancan con ids 2, 3, ...

```python
def init_db() -> None:
    """Crea las tablas (si no existen) y aplica migraciones livianas."""
    from . import models  # noqa: F401  (registra los modelos en Base)

    Base.metadata.create_all(bind=engine)
    _ensure_user_profile_columns()
    _ensure_user_google_id_column()
```

### `backend/app/auth.py` (reescrito)
Antes era un placeholder de la Fase 0 que devolvía siempre `user_id=1`. Ahora:

- `get_current_user_id(request)`: lee `request.session["user_id"]`
  (cookie firmada por `SessionMiddleware`). Si no hay sesión, lanza
  `HTTPException(401, "No autenticado")`.
- `get_or_create_user_from_google(db, google_id, email, name, avatar)`:
  busca por `google_id`, si no encuentra busca por `email` (compatibilidad a
  futuro), y si tampoco encuentra crea un `User` nuevo. Un usuario nuevo no
  tiene filas en `user_stickers` → álbum vacío.

Como **todas las rutas existentes** (`collection`, `profile`, `nearby`,
`reports`, `stickers`, `trades`) ya dependían de
`Depends(get_current_user_id)` (por diseño, según la auditoría previa),
reemplazar esta única función alcanza para que **todos** los endpoints queden
asociados al usuario logueado y protegidos con 401 — sin tocar esos archivos.

### `backend/app/schemas.py`
Dos esquemas nuevos:

```python
class GoogleLoginRequest(BaseModel):
    """Credential (ID token JWT) entregado por Google Identity Services."""
    credential: str

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    avatar: str | None
```

### `backend/app/routes/auth.py` (nuevo)
Router `prefix="/api/auth"`:

- **`POST /api/auth/google`**: recibe `{ credential }`, valida el ID token
  con `google.oauth2.id_token.verify_oauth2_token(credential, Request(),
  GOOGLE_CLIENT_ID)`. Si `GOOGLE_CLIENT_ID` no está configurado → 500. Si el
  token es inválido → 401. Si es válido, hace
  `get_or_create_user_from_google(...)`, guarda
  `request.session["user_id"] = user.id` y devuelve `UserOut`.
- **`GET /api/auth/me`**: `Depends(get_current_user_id)` → 401 si no hay
  sesión; si hay, devuelve `UserOut` del usuario actual.
- **`POST /api/auth/logout`**: `request.session.pop("user_id", None)`,
  devuelve `{"ok": true}` (siempre 200, con o sin sesión previa).

No se guarda el JWT de Google ni ningún token en la sesión — solo el `user_id`
interno.

### `backend/app/main.py`
- Se agregó `SessionMiddleware` (cookie `sc_session`, `same_site="lax"`,
  `https_only=SESSION_COOKIE_SECURE`, `max_age=30 días`, `secret_key=
  SESSION_SECRET`).
- Orden de middlewares: `SessionMiddleware` se agrega primero (queda más
  adentro), `CORSMiddleware` se agrega después (queda más afuera, con
  `allow_credentials=True`) — así la cookie de sesión puede viajar
  cross-origin hacia/desde el origen del frontend configurado en
  `CORS_ORIGINS`.
- Se registró `auth.router`.

## 2. Cambios en el frontend

### `frontend/index.html`
Se agregó el script de Google Identity Services al `<head>`:

```html
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

(Sin paquete npm — es el flujo recomendado por Google con el botón "Sign in
with Google".)

### `frontend/src/api/client.js`
- `request()` ahora envía `credentials: "include"` en todas las llamadas
  (necesario para que el navegador adjunte/reciba la cookie `sc_session`), y
  los errores HTTP llevan `error.status` (usado por `AuthContext`/rutas
  privadas).
- Nuevas funciones: `loginWithGoogle(credential)` (`POST /api/auth/google`),
  `getMe()` (`GET /api/auth/me`), `logout()` (`POST /api/auth/logout`).

### `frontend/src/context/AuthContext.jsx` (nuevo)
`AuthProvider` expone `{ user, loading, login, logout }`:
- Al montar, llama `getMe()`; si falla (401), `user = null`.
- `login(credential)` → `loginWithGoogle(credential)`, guarda el usuario
  devuelto.
- `logout()` → `logout()` del backend, limpia `user`.

### `frontend/src/pages/Login.jsx` (nuevo)
- Si ya hay usuario logueado, redirige a `/`.
- Si no, inicializa `window.google.accounts.id` con
  `VITE_GOOGLE_CLIENT_ID` y renderiza el botón oficial de Google
  ("Continuar con Google"). El callback recibe el `credential` (ID token) y
  llama a `login(credential)` del `AuthContext`.
- Muestra error si falta `VITE_GOOGLE_CLIENT_ID` o si el login falla.

### `frontend/src/App.jsx`
- Nueva ruta pública `/login`.
- `PrivateRoute`: si `loading`, muestra "Cargando..."; si no hay `user`,
  redirige a `/login`; si hay, renderiza `<Layout />` con todas las rutas
  existentes (Inicio, Buscar, Álbum, Faltantes, Repetidas, Cambios, Cerca) sin
  cambios de diseño.

### `frontend/src/main.jsx`
Se envolvió `<App />` con `<AuthProvider>` (dentro de `<BrowserRouter>`).

### `frontend/src/components/Layout.jsx`
Header existente ahora muestra, cuando hay sesión: avatar (si Google lo dio),
nombre del usuario (truncado) y botón "Salir" (logout). Resto del layout
(nav inferior, diseño responsive) sin cambios.

### `frontend/.env.example`
Se agregó `VITE_GOOGLE_CLIENT_ID` (mismo Client ID que el backend, es público
y se incluye en el build).

## 3. Migración de base de datos

Aplicada sobre `backend/stickercontrol.db` (con backup previo, ver sección 0):

- `ALTER TABLE users ADD COLUMN google_id VARCHAR`
- `CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)`

Verificado con `PRAGMA table_info(users)` / `PRAGMA index_list(users)`:

- Columnas de `users`: `id, email, name, avatar, created_at, display_name,
  city, latitude, longitude, contact_email, contact_whatsapp, is_public,
  google_id`.
- Índices de `users`: `ix_users_google_id`, `ix_users_email`.

`master_stickers` y `user_stickers`: **sin cambios de esquema ni de datos**.
La fila `id=1` (`local@stickercontrol.local`) sigue existiendo, intacta,
ahora con `google_id=NULL`, pero quedó sin uso (ningún login de Google la
referencia).

Esta misma migración se aplica automáticamente al arrancar el backend
(`init_db()` en el evento `startup`), tanto en local como en producción —
es idempotente (usa `IF NOT EXISTS` / chequeo de `PRAGMA table_info`).

## 4. Configuración necesaria

### Backend (`backend/.env`, ver `backend/.env.example`)

| Variable | Descripción | Local | Producción |
|---|---|---|---|
| `DATABASE_URL` | Ruta SQLite | `sqlite:///./stickercontrol.db` | igual |
| `CORS_ORIGINS` | Orígenes permitidos (coma-separado) | `http://localhost:5173` | `https://skillgames.com.ar` (o el origen real del frontend) |
| `GOOGLE_CLIENT_ID` | Client ID de OAuth (Google Cloud Console) | mismo valor que `VITE_GOOGLE_CLIENT_ID` | idem |
| `SESSION_SECRET` | Secreto para firmar la cookie de sesión | generar con `python -c "import secrets; print(secrets.token_hex(32))"` | uno **distinto** por entorno |
| `SESSION_COOKIE_SECURE` | Cookie con flag `Secure` (requiere HTTPS) | `false` | `true` |

### Frontend (`frontend/.env`, ver `frontend/.env.example`)

| Variable | Descripción |
|---|---|
| `VITE_GOOGLE_CLIENT_ID` | Mismo Client ID que `GOOGLE_CLIENT_ID` del backend. Es público (va en el bundle). |

### Google Cloud Console
Hay que crear (o reutilizar) un OAuth Client ID de tipo "Web application" y
agregar como "Authorized JavaScript origins":
- `http://localhost:5173` (desarrollo)
- `https://skillgames.com.ar` (producción)

No se necesita `GOOGLE_CLIENT_SECRET` ni "Authorized redirect URIs": el flujo
usado es **Google Identity Services / ID token** (el frontend recibe el
`credential` directamente y el backend lo valida con `verify_oauth2_token`),
no el flujo de código de autorización.

Ninguno de estos archivos `.env` existe todavía en el repo (`backend/.env`,
`frontend/.env` no están creados localmente, y están en `.gitignore` junto
con `backend/*.db`). Hay que crearlos a partir de los `.env.example` antes de
correr la app con login real.

## 5. Verificación

### Backend (smoke test automatizado, base SQLite temporal)
Se escribió y corrió un script temporal (`backend/_smoke_test_auth.py`,
eliminado al finalizar) que:
- Monkeypatchea `verify_oauth2_token` para simular dos logins de Google
  distintos (Usuario A / Usuario B) sin credenciales reales.
- Siembra un `MasterSticker` de prueba.

Resultado: **19/19 checks OK**, cubriendo:

- [x] Endpoints privados (`/api/auth/me`, `/api/profile`, `/api/reports/album`,
  `/api/collection/{id}/paste`, etc.) devuelven **401 sin sesión**.
- [x] `POST /api/auth/google` con credential inválido → 401.
- [x] Usuario A inicia sesión (mock) → álbum vacío.
- [x] `GET /api/auth/me` devuelve los datos del Usuario A.
- [x] Usuario A marca (pega) una figurita → álbum muestra 1 pegada.
- [x] "Refresh" (nuevo `TestClient` reutilizando la cookie de sesión) preserva
  la sesión y los datos de A.
- [x] Logout → `GET /api/auth/me` vuelve a dar 401.
- [x] Usuario B inicia sesión (mock, otro `google_id`) → usuario distinto,
  álbum vacío, **no ve la colección de A** (aislamiento por `user_id` en
  `user_stickers`).

### Backend (sobre la base real, post-migración)
Con el servidor real (`stickercontrol.db` migrada) levantado:

```
GET  /                          → 200 {"status":"ok","app":"StickerControl 2026"}
GET  /api/auth/me   (sin sesión) → 401
GET  /api/profile   (sin sesión) → 401
GET  /api/reports/album (sin sesión) → 401
GET  /api/stickers/search (sin sesión) → 401
POST /api/auth/logout (sin sesión) → 200 {"ok": true}
```

Arranque limpio, sin errores de migración ni de importación (`google-auth`,
`itsdangerous`, `requests` resuelven correctamente en `.venv`).

### Frontend
- `npm run build` → **OK** (`dist/assets/index-*.css`, `index-*.js`
  generados sin errores ni warnings de TypeScript/ESLint nuevos).
- Diseño y layout responsive existentes sin cambios (`Layout.jsx` solo agrega
  el bloque de usuario/logout en el header existente).

### Pendiente de verificación manual (requiere credenciales reales)
- Login real con Google (popup/botón GIS) en `http://localhost:5173`, con
  `GOOGLE_CLIENT_ID` / `VITE_GOOGLE_CLIENT_ID` configurados en Google Cloud
  Console con ese origin autorizado.
- Lo mismo en producción (`https://skillgames.com.ar`), con
  `SESSION_COOKIE_SECURE=true` y `CORS_ORIGINS` incluyendo ese origen.
- Verificación visual de "Usuario A ve álbum vacío → marca figurita → Usuario
  B ve álbum vacío y no ve la figurita de A" con cuentas de Google reales (la
  lógica está cubierta por el smoke test con mocks; falta el recorrido
  end-to-end en navegador).

## 6. Resumen de archivos modificados/creados

**Backend**
- `backend/requirements.txt` (modificado)
- `backend/app/models.py` (modificado — `User.google_id`)
- `backend/app/database.py` (modificado — migración `google_id`, `init_db`
  sin usuario por defecto)
- `backend/app/auth.py` (reescrito)
- `backend/app/schemas.py` (modificado — `GoogleLoginRequest`, `UserOut`)
- `backend/app/routes/auth.py` (nuevo)
- `backend/app/main.py` (modificado — `SessionMiddleware`, router `auth`)
- `backend/.env.example` (reescrito)
- `backend/stickercontrol.db` (migrado; backup en
  `backend/stickercontrol.db.bak-fase2a-20260615-134401`)

**Frontend**
- `frontend/index.html` (modificado — script GIS)
- `frontend/src/api/client.js` (modificado — `credentials: include`,
  `loginWithGoogle`, `getMe`, `logout`)
- `frontend/src/context/AuthContext.jsx` (nuevo)
- `frontend/src/pages/Login.jsx` (nuevo)
- `frontend/src/App.jsx` (modificado — ruta `/login`, `PrivateRoute`)
- `frontend/src/main.jsx` (modificado — `AuthProvider`)
- `frontend/src/components/Layout.jsx` (modificado — header con
  usuario/logout)
- `frontend/.env.example` (modificado — `VITE_GOOGLE_CLIENT_ID`)

## 7. No incluido en esta fase (a propósito)

- Chat / mensajería entre usuarios.
- Solicitudes de intercambio.
- Cualquier otra función social nueva (usuarios cercanos ya existía de una
  fase previa y sigue intacta, ahora también queda automáticamente
  user-scoped por el cambio en `get_current_user_id`).
- Borrado de la fila huérfana `id=1` (`local@stickercontrol.local`): se deja
  como está, sin uso, para no realizar ningún borrado de datos no solicitado.
