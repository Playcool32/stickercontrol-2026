# Auditoría Fase 2B — Link público de solo lectura

**Fecha:** 2026-06-16  
**Estado:** Auditoría únicamente — sin cambios de código todavía.

---

## 1. Resumen ejecutivo

El usuario logueado genera un token opaco (`share_token`) que activa endpoints
públicos de solo lectura. Cualquier visitante que tenga el link puede ver el
álbum, faltantes y repetidas **sin login y sin poder editar nada**.

El cambio es **aditivo en todos los niveles**:
- DB: una columna nueva en `users` (ALTER TABLE, mismo patrón de Fase 2A)
- Backend: un router nuevo (`/api/public/`, `/api/share/`), sin tocar rutas existentes
- Frontend: una ruta nueva (`/share/:token`) fuera de `PrivateRoute`, sin tocar el shell ni las páginas privadas

---

## 2. Arquitectura actual relevante

### Backend

| Archivo | Relevante para Fase 2B |
|---|---|
| `models.py` | `User` — necesita columna `share_token` |
| `database.py` | `init_db()` — debe agregar `_ensure_share_token_column()` |
| `routes/reports.py` | `get_album()`, `get_missing()`, `get_duplicates()` — la lógica real; se reutiliza sin modificar |
| `auth.py` | `get_current_user_id()` — solo para el endpoint de generación (el usuario debe estar logueado para generar su token) |
| `main.py` | Necesita `include_router(share.router)` |

### Frontend

| Archivo | Relevante para Fase 2B |
|---|---|
| `App.jsx` | Necesita ruta `/share/:token` fuera de `PrivateRoute` |
| `api/client.js` | Necesita 4 funciones nuevas (sin `credentials: "include"`) |
| `pages/Dashboard.jsx` | Necesita botón "Compartir mi álbum" |
| `pages/Album.jsx` | `CountryCard` tiene botones interactivos — en la vista pública se renderizan read-only |
| `components/Layout.jsx` | **NO se toca** — la vista pública tiene su propio layout mínimo |

---

## 3. Diseño del token

| Decisión | Valor |
|---|---|
| Generación | `secrets.token_urlsafe(16)` → 22 chars URL-safe (128 bits de entropía) |
| Almacenamiento | `users.share_token VARCHAR UNIQUE NULL` |
| Semántica | `NULL` = el usuario nunca generó link. Asignado al llamar `POST /api/share/generate`. |
| Revocación | Fuera de alcance MVP. El token persiste hasta que se implemente reset. |
| Visibilidad | Solo el propietario ve su token (endpoint autenticado). El visitante lo recibe en la URL compartida. |

URL resultante en producción:
```
https://skillgames.com.ar/stickercontrol/share/<token>
```

---

## 4. Cambios de backend

### 4.1 `backend/app/models.py`

Agregar campo a `User`:

```python
share_token: Mapped[str | None] = mapped_column(
    String, unique=True, index=True, nullable=True
)
```

Un campo, al final del modelo. El índice único previene colisiones (extremadamente improbables con 128 bits, pero es la práctica correcta).

### 4.2 `backend/app/database.py`

Nueva función (mismo patrón que `_ensure_user_google_id_column`):

```python
def _ensure_share_token_column() -> None:
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "share_token" not in existing:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN share_token VARCHAR")
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_share_token ON users (share_token)"
        )
        conn.commit()
```

Llamada desde `init_db()`:
```python
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_user_profile_columns()
    _ensure_user_google_id_column()
    _ensure_share_token_column()   # ← nueva línea
```

### 4.3 `backend/app/schemas.py`

Dos schemas nuevos, al final del archivo:

```python
class ShareTokenResponse(BaseModel):
    token: str

class PublicOwnerResponse(BaseModel):
    owner_name: str
```

Los endpoints públicos de álbum/faltantes/repetidas reutilizan
`AlbumResponse`, `MissingResponse`, `DuplicatesResponse` sin modificarlos.

### 4.4 `backend/app/routes/share.py` — archivo nuevo

Dos responsabilidades en un router:

**A) Endpoint autenticado — genera el token:**

```
POST /api/share/generate
  → Depends(get_current_user_id)
  → Si users.share_token IS NULL: genera secrets.token_urlsafe(16), persiste
  → Devuelve ShareTokenResponse { token }
```

Idempotente: si el usuario ya tiene token, devuelve el mismo.

**B) Endpoints públicos — sin auth, sin cookie:**

```
GET /api/public/{token}             → PublicOwnerResponse { owner_name }
GET /api/public/{token}/album       → AlbumResponse
GET /api/public/{token}/missing     → MissingResponse
GET /api/public/{token}/duplicates  → DuplicatesResponse
```

Todos los públicos:
- Buscan al usuario por `users.share_token = token`
- Si no existe → 404 `{"detail": "Álbum no encontrado"}`
- Llaman la misma lógica interna que los endpoints privados, con el `user_id` del dueño del token
- **No requieren** `Depends(get_current_user_id)`

La implementación interna reutiliza las funciones del módulo `reports`:

```python
# En routes/share.py:
from .reports import get_album as _get_album_impl
# ... pero get_album() es un endpoint FastAPI, no una función reutilizable.
```

En la práctica, `routes/reports.py` expone los endpoints directamente con lógica embebida.
La solución limpia sin refactorizar `reports.py` es **duplicar las 3-4 líneas de lógica** en
`share.py`, usando las mismas imports (`_all_stickers_with_status`, `_country_sort_key`, etc.)
extraídas como helpers del mismo módulo.

**Alternativa sin duplicar:** mover la lógica de negocio a `crud.py` o a un módulo
`services/reports.py`. Pero eso toca `reports.py`, y la restricción dice no modificar
rutas existentes. **Decisión: duplicar las ~15 líneas de lógica en `share.py`** — son
funciones puras (`_all_stickers_with_status`, `build_country`), sin estado, seguras de
copiar. No es "duplicación permanente" problemática: si en el futuro se quiere extraer,
es refactor acotado.

### 4.5 `backend/app/main.py`

Una línea:

```python
from .routes import auth, collection, nearby, profile, reports, share, stickers, trades
# ...
app.include_router(share.router)
```

---

## 5. Cambios de frontend

### 5.1 `frontend/src/api/client.js`

Cuatro funciones nuevas. Las públicas **no usan** `credentials: "include"` ni el
`request()` helper (que manda cookies):

```js
// Autenticada: el usuario logueado genera su token
export function generateShareToken() {
  return request("/share/generate", { method: "POST" });
}

// Públicas: no mandan cookies, usan fetch directo
const PUBLIC_BASE = `${import.meta.env.BASE_URL}api/public`;

export async function getPublicOwner(token) {
  const res = await fetch(`${PUBLIC_BASE}/${token}`);
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

export async function getPublicAlbum(token) {
  const res = await fetch(`${PUBLIC_BASE}/${token}/album`);
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

export async function getPublicMissing(token) {
  const res = await fetch(`${PUBLIC_BASE}/${token}/missing`);
  if (!res.ok) throw new Error(res.status);
  return res.json();
}

export async function getPublicDuplicates(token) {
  const res = await fetch(`${PUBLIC_BASE}/${token}/duplicates`);
  if (!res.ok) throw new Error(res.status);
  return res.json();
}
```

### 5.2 `frontend/src/App.jsx`

Una ruta nueva, **fuera de `PrivateRoute`**, al mismo nivel que `/login`:

```jsx
import ShareView from "./pages/ShareView.jsx";

// En <Routes>:
<Route path="/login" element={<Login />} />
<Route path="/share/:token" element={<ShareView />} />   {/* ← nueva */}
<Route element={<PrivateRoute><Layout /></PrivateRoute>}>
  ...rutas privadas sin cambios...
</Route>
```

El visitante llega a `/share/<token>` → React Router renderiza `ShareView` directamente,
sin pasar por `PrivateRoute`, sin redirigir a `/login`.

### 5.3 `frontend/src/pages/ShareView.jsx` — archivo nuevo

Estructura de la página pública:

```
┌─────────────────────────────────────────┐
│  StickerControl 2026  [readonly badge]  │  ← header mínimo (sin nav, sin logout)
├─────────────────────────────────────────┤
│  Álbum de <owner_name>                  │
│  [ProgressRing]  X/980 pegadas (Y%)     │
├─────────────────────────────────────────┤
│  [Álbum] [Faltantes] [Repetidas]        │  ← tabs simples
├─────────────────────────────────────────┤
│  <contenido del tab activo>             │
└─────────────────────────────────────────┘
```

Comportamiento:
- Monta → llama `getPublicOwner(token)` para el nombre
- Tab "Álbum" → llama `getPublicAlbum(token)` → reutiliza `CountryCard` pero con `onSelectSticker={null}` (sin modal)
- Tab "Faltantes" → llama `getPublicMissing(token)` → misma UI de `Missing.jsx` pero sin botón "Copiar WhatsApp" (o con él — es info pública)
- Tab "Repetidas" → llama `getPublicDuplicates(token)` → misma UI de `Duplicates.jsx` pero sin botón "Copiar" (ídem)
- Si el token no existe → mensaje "Este álbum no existe o el link expiró."
- Sin `useAuth`, sin `PrivateRoute`, sin nav inferior

Los componentes `CountryCard` (de `Album.jsx`), `ProgressRing` se **reutilizan como están**. 
La diferencia es que `onSelectSticker` recibe `null` → los badges no abren modal 
(o abren un modal read-only sin botones de acción, si se quiere "navegar").

Para MVP: badges no clickeables en la vista pública (se pasan como `<div>` en vez de `<button>`).

### 5.4 `frontend/src/pages/Dashboard.jsx`

Agregar sección "Compartir mi álbum" debajo de los accesos rápidos:

```
┌─────────────────────────────────────┐
│  🔗 Compartir mi álbum              │
│  [Generar link]                     │
│  → una vez generado:                │
│  skillgames.com.ar/stickercontrol/  │
│  share/<token>   [Copiar link]      │
└─────────────────────────────────────┘
```

Lógica:
- Al montar, llama `GET /api/share/generate` — no: eso generaría el token sin que el usuario lo pida
- Mejor: botón "Generar link" → `POST /api/share/generate` → muestra la URL → botón "Copiar"
- Si ya tiene token (guardado en estado), muestra directamente la URL
- Estado local `shareToken` (no persistido en localStorage — se recupera llamando al endpoint)

**Consideración UX:** el token se genera una vez y persiste. Al recargar `Dashboard`, el botón vuelve a decir "Generar link" (el token está en la DB pero no en el cliente). Podría simplificarse con un `GET /api/share/token` que devuelve el token existente (o null), para mostrarlo directamente si ya existe. Esto requiere un endpoint GET adicional de bajo costo.

**Decisión para MVP:** agregar `GET /api/share/token` → devuelve `{token}` si existe o `{token: null}`. `Dashboard` lo llama al montar y muestra el estado correcto.

---

## 6. Archivos a tocar — resumen

| Archivo | Tipo | Cambio |
|---|---|---|
| `backend/app/models.py` | modificar | `share_token` en `User` |
| `backend/app/database.py` | modificar | `_ensure_share_token_column()` + llamada en `init_db()` |
| `backend/app/schemas.py` | modificar | `ShareTokenResponse`, `PublicOwnerResponse` |
| `backend/app/routes/share.py` | **NUEVO** | `POST /api/share/generate`, `GET /api/share/token`, 4 endpoints públicos |
| `backend/app/main.py` | modificar | `include_router(share.router)` |
| `frontend/src/api/client.js` | modificar | 5 funciones nuevas |
| `frontend/src/App.jsx` | modificar | ruta `/share/:token` |
| `frontend/src/pages/ShareView.jsx` | **NUEVO** | vista pública read-only |
| `frontend/src/pages/Dashboard.jsx` | modificar | sección "Compartir mi álbum" |

**Total: 9 archivos — 2 nuevos, 7 modificados.**

---

## 7. Endpoints completos

### Autenticados (requieren sesión)

| Método | Path | Descripción |
|---|---|---|
| `POST` | `/api/share/generate` | Genera o devuelve el `share_token` del usuario actual |
| `GET` | `/api/share/token` | Devuelve `{token}` del usuario actual (null si no tiene) |

### Públicos (sin sesión, sin cookie)

| Método | Path | Descripción |
|---|---|---|
| `GET` | `/api/public/{token}` | Nombre del dueño del álbum |
| `GET` | `/api/public/{token}/album` | Álbum completo (mismo schema que `/api/reports/album`) |
| `GET` | `/api/public/{token}/missing` | Faltantes (mismo schema que `/api/reports/missing`) |
| `GET` | `/api/public/{token}/duplicates` | Repetidas (mismo schema que `/api/reports/duplicates`) |

**Todos los endpoints públicos devuelven 404 si el token no existe.**

---

## 8. Migración de DB

```sql
-- Aplicada automáticamente en init_db() al arrancar el backend:
ALTER TABLE users ADD COLUMN share_token VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_share_token ON users (share_token);
```

- Aditiva, idempotente, sin Alembic.
- `share_token = NULL` para todos los usuarios existentes (no se genera automáticamente).
- No afecta `user_stickers`, `master_stickers`, ni ninguna lógica existente.

---

## 9. Riesgos y consideraciones

### Riesgo: `notes` expuestas en la vista pública

`StickerOut.notes` es parte del schema de álbum y se expone en los endpoints públicos
(igual que en los privados). Si el usuario escribió notas personales (ej: "regalo de
mamá", "conseguir con vecino"), aparecerán visibles en el link compartido.

**Opciones:**
- A (MVP, simple): exponer notes — el usuario eligió compartir su álbum, es su decisión.
- B (segura): filtrar `notes=None` en los endpoints públicos antes de serializar.

**Recomendación: opción B** — costo mínimo (una línea en `share.py` al construir
el `StickerOut`), evita sorpresa desagradable al usuario. No requiere schema nuevo.

### Riesgo: token predecible

`secrets.token_urlsafe(16)` = 128 bits de entropía. Con 1M de usuarios activos y
1B de requests por segundo, el tiempo esperado para colisión por fuerza bruta es
de ~1.7×10²⁰ años. **Riesgo: despreciable.**

### Riesgo: el token no expira

El link es permanente hasta que se implemente revocación. Para el Mundial (uso
intensivo por semanas), esto es aceptable. Si el usuario quiere "cerrar" su álbum
público, no puede en el MVP.

**Mitigación futura:** `POST /api/share/reset` que genera un token nuevo (invalida
el anterior). No requiere nueva columna.

### Riesgo: router `/api/public/` sin CORS conflict

Los endpoints públicos no usan cookies. El middleware de CORS actual permite
`allow_origins=[origen del frontend]`. Cualquier visitante que acceda desde otro
origen (ej: el link compartido en WhatsApp, abierto en el navegador) también pasa
por CORS. En el deploy real, el visitante accede desde
`https://skillgames.com.ar`, mismo origen que el frontend → sin problema.

Si el visitante abre el link desde otro dispositivo/origen: CORS bloqueará.
**Solución:** los endpoints `/api/public/*` deben ser accesibles desde cualquier
origen. Dos opciones:
- A: `allow_origins=["*"]` en un `CORSMiddleware` adicional solo para `/api/public/*`
- B: añadir `*` al `CORS_ORIGINS` del `.env` → afectaría todos los endpoints

**Recomendación: opción A** — montar el sub-router de public con su propio
`CORSMiddleware`. Esto en FastAPI se hace con un `APIRouter` o con un mini `app`
montado en `/api/public`. **Alternativa más simple:** dado que los endpoints
públicos no mandan ni reciben cookies, pueden responder a cualquier origen sin
riesgo de seguridad. Agregar un header `Access-Control-Allow-Origin: *`
manualmente en la respuesta, o usar un decorator.

**Solución más simple en FastAPI:** agregar el origin `*` como excepción solo
para las rutas `/api/public/*` usando un middleware condicional, o simplemente
ampliar `CORS_ORIGINS` para incluir `*`. Para el MVP bajo `skillgames.com.ar`,
el visitante siempre viene del mismo origen → no hay problema real en producción.
Documentar como consideración a revisar si se comparte fuera del sitio.

### Riesgo: nginx y SPA fallback

La ruta `/stickercontrol/share/<token>` la maneja el frontend (React Router).
El bloque `try_files` de nginx ya cubre este caso:
```nginx
try_files $uri $uri/ /stickercontrol/index.html;
```
No requiere cambios en nginx.

### Lo que NO se toca

| Componente | Estado |
|---|---|
| Google Login / auth / sesión | **NO TOCADO** |
| Rutas privadas existentes | **NO TOCADO** |
| `reports.py` (lógica existente) | **NO TOCADO** |
| `user_stickers` (esquema y filas) | **NO TOCADO** |
| Responsive / mobile | **NO TOCADO** |
| nginx / VPS | **NO TOCADO** |

---

## 10. Plan de implementación (orden de ejecución)

```
PASO 1 — Backend (sin tocar nada existente):
  a. models.py       → campo share_token en User
  b. database.py     → _ensure_share_token_column() + init_db()
  c. schemas.py      → ShareTokenResponse, PublicOwnerResponse
  d. routes/share.py → todos los endpoints (autenticados + públicos)
  e. main.py         → include_router(share.router)

PASO 2 — Frontend:
  a. api/client.js   → 5 funciones nuevas
  b. App.jsx         → ruta /share/:token
  c. ShareView.jsx   → página pública nueva
  d. Dashboard.jsx   → sección "Compartir mi álbum"

PASO 3 — Verificaciones:
  a. npm run build → OK
  b. Backend arranca, init_db() aplica migración, columna share_token existe
  c. POST /api/share/generate (autenticado) → token generado
  d. GET /api/share/token → devuelve el token
  e. GET /api/public/{token} → owner_name
  f. GET /api/public/{token}/album → mismos datos que /api/reports/album
  g. GET /api/public/{token}/missing → mismos datos que /api/reports/missing
  h. GET /api/public/{token}/duplicates → mismos datos que /api/reports/duplicates
  i. GET /api/public/{token_invalido} → 404
  j. /share/:token en browser → renderiza sin login, sin nav privado
  k. Los badges del álbum son read-only (no hay acciones de pegar/despegar)
  l. Rutas privadas siguen funcionando igual (no regresión)
```

---

## 11. Decisiones pendientes de confirmar antes de implementar

1. **¿Exponer `notes` en la vista pública?**
   Recomendación: NO (filtrar `notes=None` en endpoints públicos). Costo: mínimo.

2. **¿Botón "Copiar para WhatsApp" en Faltantes/Repetidas de la vista pública?**
   Esa función es útil también para el visitante (puede querer copiar la lista).
   Recomendación: SÍ, mantenerlo — es información pública y es UX útil.

3. **¿Modal de detalle de figurita en la vista pública?**
   Abrir el modal mostraría el código, nombre, estado (pero sin botones de acción).
   Recomendación: NO para MVP — badges como `<div>` no clickeables. Simplifica el componente.

4. **¿`GET /api/share/token` para saber si el usuario ya tiene token?**
   Recomendación: SÍ — evita que el Dashboard muestre siempre "Generar link" aunque
   el token ya exista. Costo: 5 líneas en share.py.

5. **CORS para endpoints públicos:**
   En el entorno actual (todo bajo `skillgames.com.ar`), no hay problema real.
   Recomendación: no agregar CORS especial ahora; documentar para cuando se comparta externamente.
