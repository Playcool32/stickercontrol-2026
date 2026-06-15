# Checkpoint de deploy — Google Login multiusuario (Fase 2A)

**Fecha:** 2026-06-15
**Branch:** `main`
**Commit:** `ec5beb367b92180766fd5048e6ac89d6f2b976fd` (`ec5beb3` corto) —
"StickerControl 2026 - Fase 2A Google Login multiusuario"

## Tags

- `v0.9-single-user-stable` → `04bf1bde2e6b38802b498b588053d524a39bdb46`
  (`12ca619`). Última versión single-user, sin login. Punto de rollback.
  Ver `RELEASE_v0.9_SINGLE_USER.md`.
- `v1.0-google-login-beta` → `ec5beb367b92180766fd5048e6ac89d6f2b976fd`
  (`ec5beb3`). Versión con Google Login / multiusuario, lista para probar
  en producción.

Ambos tags y `main` ya están pusheados a
`https://github.com/Playcool32/stickercontrol-2026`.

## Resumen de cambios (Fase 2A)

Detalle completo en `GOOGLE_LOGIN_IMPLEMENTATION_REPORT.md`. Resumen:

- **Google Login**: nuevo router `/api/auth` —
  `POST /api/auth/google` (valida el ID token de Google Identity Services y
  crea/actualiza el usuario), `GET /api/auth/me`, `POST /api/auth/logout`.
- **Sesiones**: `SessionMiddleware` (Starlette) con cookie `sc_session`
  (httpOnly, `SameSite=Lax`, `Secure` configurable, 30 días de duración).
- **`AuthContext`** (frontend): expone `user`, `loading`, `login`, `logout`;
  hace `GET /api/auth/me` al montar la app.
- **Logout**: botón "Salir" en el header (`Layout.jsx`), llama a
  `POST /api/auth/logout` y limpia el estado de usuario.
- **Rutas protegidas**: `PrivateRoute` en `App.jsx` redirige a `/login` si no
  hay usuario autenticado. Nueva página pública `/login` con el botón
  "Continuar con Google".
- **Multiusuario**: `get_current_user_id()` ahora lee el `user_id` de la
  sesión (401 si no hay sesión). Todos los endpoints existentes
  (`collection`, `profile`, `nearby`, `reports`, `stickers`, `trades`) ya
  dependían de esta función, así que quedaron automáticamente user-scoped:
  cada usuario ve y modifica solo su propia colección (`user_stickers`).
  `master_stickers` sigue siendo global, sin cambios.
- **DB**: migración aditiva — `users.google_id` (nullable, único, indexado).
  Se aplica sola al arrancar el backend (`init_db()`), es idempotente.
  No afecta `master_stickers` ni los códigos.

No se tocó diseño, mobile/responsive, "Usuarios cerca" ni intercambios —
solo quedaron protegidos por sesión, sin cambios funcionales propios.

## Variables necesarias en producción

### Backend (`backend/.env`, ver `backend/.env.example`)

| Variable | Valor en producción |
|---|---|
| `DATABASE_URL` | `sqlite:///./stickercontrol.db` (sin cambios) |
| `CORS_ORIGINS` | `https://www.skillgames.com.ar` (origen real del frontend) |
| `GOOGLE_CLIENT_ID` | Client ID de OAuth de Google Cloud Console (tipo "Web application") |
| `SESSION_SECRET` | Secreto único para producción — generar con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SESSION_COOKIE_SECURE` | `true` (el sitio usa HTTPS) |

### Frontend (`frontend/.env`, ver `frontend/.env.example`)

| Variable | Valor en producción |
|---|---|
| `VITE_GOOGLE_CLIENT_ID` | **Mismo** Client ID que `GOOGLE_CLIENT_ID` del backend (es público, va en el bundle) |

### Google Cloud Console

El OAuth Client ID debe tener `https://www.skillgames.com.ar` (y
`http://localhost:5173` para desarrollo) en "Authorized JavaScript origins".
No se necesita `GOOGLE_CLIENT_SECRET` ni redirect URIs (flujo de ID token de
Google Identity Services).

## Procedimiento de actualización en el VPS

```bash
cd /var/www/skillgames/stickercontrol-2026

# 1. Traer el código nuevo
git fetch origin
git checkout main
git pull origin main

# 2. Backend: configurar .env (si no existe, copiar desde .env.example y
#    completar GOOGLE_CLIENT_ID / SESSION_SECRET / SESSION_COOKIE_SECURE=true
#    / CORS_ORIGINS). Instalar dependencias nuevas (google-auth,
#    itsdangerous, requests).
cd backend
source .venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. Frontend: configurar .env (VITE_GOOGLE_CLIENT_ID), instalar y compilar.
cd frontend
# crear/editar .env con VITE_GOOGLE_CLIENT_ID antes de build
npm install
npm run build
cd ..

# 4. Reiniciar servicios
systemctl restart stickercontrol-backend
systemctl reload nginx
```

Notas:
- La migración de `users.google_id` se aplica sola al reiniciar el backend
  (`init_db()` en el evento `startup`). No requiere pasos manuales de SQL.
- Antes de reiniciar, conviene tener un backup de
  `backend/stickercontrol.db` (ej. `cp stickercontrol.db
  stickercontrol.db.bak-prod-$(date +%Y%m%d-%H%M%S)`), igual que se hizo en
  desarrollo.
- `npm install` es necesario porque no hubo cambios de `package.json` en
  Fase 2A (Google Identity Services se carga vía `<script>` en `index.html`,
  sin paquete npm nuevo), pero se incluye en el procedimiento estándar por si
  difiere `node_modules` del VPS.

## Plan de prueba real (dos cuentas de Google)

**Cuenta Google A**
- [ ] Ir a `/login`, click en "Continuar con Google", iniciar sesión con la
  cuenta A.
- [ ] Verificar que redirige al álbum y que el álbum aparece **vacío**
  (usuario nuevo).
- [ ] Marcar (pegar) una figurita.
- [ ] Refrescar la página (F5) → la sesión se mantiene (sigue logueado) y la
  figurita marcada sigue apareciendo.
- [ ] `GET /api/auth/me` devuelve los datos de la cuenta A.
- [ ] Logout (botón "Salir") → vuelve a `/login`.

**Cuenta Google B** (otra cuenta de Google, distinta de A)
- [ ] Login con la cuenta B.
- [ ] Verificar álbum **vacío** (no debe ver la figurita marcada por A).
- [ ] (Opcional) Marcar una figurita distinta con B.
- [ ] Logout.

**Volver con cuenta A**
- [ ] Login nuevamente con la cuenta A.
- [ ] Verificar que su colección sigue intacta (la figurita marcada antes
  sigue marcada, y no aparece nada de lo que marcó B).

**Endpoints sin sesión**
- [ ] Sin estar logueado, navegar directo a `/album` (o cualquier ruta
  privada) → redirige a `/login`.
- [ ] (Opcional, vía curl/devtools) `GET /api/profile` sin cookie de sesión
  → `401`.

## Rollback de emergencia

Si el login con Google falla en producción (errores de `GOOGLE_CLIENT_ID`,
CORS, cookies, etc.) y se necesita volver rápido a la versión sin login:

```bash
cd /var/www/skillgames/stickercontrol-2026

git checkout v0.9-single-user-stable

cd frontend
npm run build
cd ..

systemctl restart stickercontrol-backend
systemctl reload nginx
```

Después de esto la app vuelve a funcionar en modo single-user (sin login),
como antes de la Fase 2A — ver `RELEASE_v0.9_SINGLE_USER.md` para el detalle
de esa versión y cómo retomar `main` luego.

La migración `users.google_id` (si ya se aplicó) es aditiva y no afecta al
código de `v0.9` — no es necesario restaurar el `.db` para que el rollback de
código funcione.
