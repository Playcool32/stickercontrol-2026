# Fase 0.6.2 — Preparación para deploy bajo SkillGames

Objetivo cumplido: StickerControl 2026 queda preparado para funcionar bajo
`https://www.skillgames.com.ar/stickercontrol`, sin agregar login, chat,
OAuth ni invitaciones.

## 1. Bug de privacidad corregido (B1 de la auditoría forense)

`GET /api/nearby/{user_id}/contact-message` ahora devuelve **404** si el
usuario objetivo no existe **o** no tiene `is_public=true` — el mismo
status/detalle (`"Usuario no encontrado"`) en ambos casos, para no revelar
si existe un perfil privado con ese id (recomendación R2 de
`NEARBY_FORENSIC_TEST.md`).

`backend/app/routes/nearby.py::get_contact_message`:

```python
other = db.get(models.User, other_user_id)
if other is None or not other.is_public:
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
```

Verificado con base temporal (3 usuarios: yo=privado, vecino público,
privado con contacto):

- `GET /api/nearby/2/contact-message` (público) → `200` con texto + links
- `GET /api/nearby/3/contact-message` (privado) → `404`
- `GET /api/nearby/999/contact-message` (inexistente) → `404`

## 2. Exposición de contacto eliminada de `/api/nearby`

`NearbyUser` ya **no** incluye `contact_email`/`contact_whatsapp` en texto
plano. Se reemplazaron por booleanos:

```python
has_email: bool
has_whatsapp: bool
```

calculados como `bool(other.contact_email)` / `bool(other.contact_whatsapp)`
en `routes/nearby.py::get_nearby`.

`ContactMessageResponse` ahora genera los enlaces **en el servidor**, con
`urllib.parse.quote(text, safe="")`:

```python
class ContactMessageResponse(BaseModel):
    text: str
    whatsapp_url: str | None
    mailto_url: str | None
```

- `whatsapp_url = https://wa.me/{contact_whatsapp}?text={texto codificado}`
  (solo si `contact_whatsapp` está seteado)
- `mailto_url = mailto:{contact_email}?subject=Intercambio...&body={texto}`
  (solo si `contact_email` está seteado)

**Frontend** (`pages/Nearby.jsx`):

- Las tarjetas muestran botones "Contactar por WhatsApp"/"Contactar por
  email" según `has_whatsapp`/`has_email` (ya no según el dato crudo).
- Al hacer click, `getContactMessage(userId)` trae `text` +
  `whatsapp_url`/`mailto_url` y los usa directamente — el frontend ya no
  construye los links ni ve `contact_email`/`contact_whatsapp` de otros
  usuarios en ningún momento.

Verificado: `/api/nearby` para el vecino público devuelve
`"has_email":true,"has_whatsapp":true` (sin los valores reales), y
`/api/nearby/2/contact-message` devuelve `whatsapp_url`/`mailto_url`
correctamente codificados (`%0A`, `%3A`, `%C2%BF`, etc.).

## 3. Vite — base path `/stickercontrol/`

`frontend/vite.config.js` ahora exporta una función dependiente de `mode`:

```js
export default defineConfig(({ mode }) => ({
  base: mode === "production" ? "/stickercontrol/" : "/",
  ...
}));
```

`vite build` usa `mode="production"` por defecto → `base: "/stickercontrol/"`.
`vite dev`/`vite preview --mode development` (o sin flag, dev) → `base: "/"`.

## 4. React Router con `basename`

`frontend/src/main.jsx`:

```js
const basename = import.meta.env.BASE_URL.replace(/\/$/, "");

<BrowserRouter basename={basename}>
  <App />
</BrowserRouter>
```

- Dev: `BASE_URL="/"` → `basename=""` (rutas tal cual: `/`, `/cerca`, etc.)
- Prod: `BASE_URL="/stickercontrol/"` → `basename="/stickercontrol"` (rutas
  reales: `/stickercontrol/`, `/stickercontrol/cerca`, etc.)

No se modificaron `App.jsx` ni `Layout.jsx` — las rutas internas (`to="/cerca"`,
etc.) siguen siendo relativas al `basename`, React Router las resuelve solo.

## 5. Cliente API

`frontend/src/api/client.js`:

```js
const BASE_URL = `${import.meta.env.BASE_URL}api`;
```

- Dev: `"/" + "api"` = `/api` (proxy de Vite hacia `:8000`, sin cambios)
- Prod: `"/stickercontrol/" + "api"` = `/stickercontrol/api` (proxificado por
  nginx hacia el backend, ver `DEPLOY.md`)

## 6. Landing en el Dashboard

`frontend/src/pages/Dashboard.jsx` agrega, antes del resumen existente, un
bloque de bienvenida:

- Título: **"Controlá tus figuritas del Mundial 2026"**
- Bullets: **"Pegadas, faltantes, repetidas"** / **"Usuarios cerca para
  intercambiar"**
- Botón **"Empezar"** → enlaza a `/buscar`

El resto del Dashboard (resumen de colección, accesos rápidos) queda igual.

## 7. `DEPLOY.md` actualizado

Reescrito con ejemplo real para SkillGames:

- Backend: systemd (`stickercontrol-backend.service`, uvicorn en
  `127.0.0.1:8000`), `.env` con `CORS_ORIGINS=https://www.skillgames.com.ar`.
- Frontend: `npm run build` (usa `base: "/stickercontrol/"` automáticamente).
- Nginx: bloque agregado al `server {}` existente de
  `www.skillgames.com.ar`:
  - `location /stickercontrol/api/` → `proxy_pass http://127.0.0.1:8000/api/;`
    (la barra final reescribe el prefijo correctamente)
  - `location /stickercontrol/` → `alias .../frontend/dist/;` +
    `try_files $uri $uri/ /stickercontrol/index.html;` (SPA fallback para
    recargar `/stickercontrol/cerca`, etc.)
- SQLite: `backend/stickercontrol.db`, backup diario vía `sqlite3 .backup`
  + cron, retención de 14 días.
- Tabla de rutas verificadas bajo `/stickercontrol`.

## 8. Pruebas ejecutadas

| Prueba | Resultado |
|---|---|
| `npm run build` | OK — `dist/index.html` referencia `/stickercontrol/assets/...` |
| `npm run preview` (sirve `dist/` con `base`) | OK — `http://localhost:4173/stickercontrol/`, `/stickercontrol/cerca`, `/stickercontrol/faltantes` → `200` |
| Backend arranca (`uvicorn app.main:app`) | OK — `GET /` → `{"status":"ok",...}` |
| `npm run dev` (modo desarrollo) | OK — `base="/"`, `basename=""`, rutas `/`, `/cerca`, `/faltantes` → `200` |
| Proxy `/api` en dev | OK — `GET /api/nearby` vía `:5174` → `{"users":[]}` |
| Schema `NearbyUser` (OpenAPI) | `has_email`, `has_whatsapp` presentes; sin `contact_email`/`contact_whatsapp` |
| Schema `ContactMessageResponse` (OpenAPI) | `text`, `whatsapp_url`, `mailto_url` |
| Privacidad: contact-message usuario privado | `404` |
| Privacidad: contact-message usuario inexistente | `404` |
| Privacidad: contact-message usuario público | `200` con `whatsapp_url`/`mailto_url` codificados |

Todas las pruebas se corrieron contra una base SQLite temporal
(`D:/tmp_sc_0_6_2.db`, eliminada al finalizar) con 3 usuarios de prueba
(yo, vecino público, usuario privado) — no se modificó la base de
desarrollo real.

## Alcance respetado

No se implementó login, chat, OAuth ni invitaciones — sin cambios en
`get_current_user_id()` (sigue devolviendo `1`), sin tablas nuevas, sin
WebSockets.

## Archivos modificados

- `backend/app/schemas.py` — `NearbyUser.has_email/has_whatsapp`,
  `ContactMessageResponse.whatsapp_url/mailto_url`
- `backend/app/routes/nearby.py` — fix de privacidad + generación de links
- `frontend/vite.config.js` — `base` dependiente de `mode`
- `frontend/src/main.jsx` — `basename` en `BrowserRouter`
- `frontend/src/api/client.js` — `BASE_URL` dinámico
- `frontend/src/pages/Nearby.jsx` — usa `has_email`/`has_whatsapp` y
  `whatsapp_url`/`mailto_url` del backend
- `frontend/src/pages/Dashboard.jsx` — landing
- `DEPLOY.md` — guía real de deploy SkillGames
