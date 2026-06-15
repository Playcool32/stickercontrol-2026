# Release v0.9-single-user-stable

**Fecha del checkpoint:** 2026-06-15
**Commit:** `04bf1bde2e6b38802b498b588053d524a39bdb46` (`12ca619` corto) —
"Restructure responsive layout without redesign"
**Tag:** `v0.9-single-user-stable`
**Branch:** `main`

## Qué es esta versión

Última versión **single-user** estable de StickerControl 2026, previa a la
implementación de Google Login / multiusuario (Fase 2A). Toda la app corre
con un único usuario implícito (`id=1`, `local@stickercontrol.local`), sin
login, sin sesiones, sin OAuth.

Sirve como punto de recuperación: si la Fase 2A (`v1.0-google-login-beta`)
falla en producción, se puede volver a este estado con la app funcionando
exactamente como antes del cambio.

## Funcionalidades incluidas

- Búsqueda de figuritas (`/buscar`, `/api/stickers/search`).
- Colección personal: pegar / despegar / incrementar / decrementar /
  marcar faltante / notas (`/api/collection/*`).
- Álbum agrupado por selección/grupo, en el orden real del sorteo
  (`/album`, `/api/reports/album`).
- Faltantes y repetidas, con texto listo para compartir por WhatsApp
  (`/faltantes`, `/repetidas`, `/api/reports/missing`,
  `/api/reports/duplicates`).
- Estado de intercambios (`/intercambios`, `/api/trades/status`).
- Perfil público opcional y "Usuarios cerca" (`/cerca`, `/api/profile`,
  `/api/nearby`), con privacidad reforzada (sin exponer contacto crudo,
  respuestas 404 uniformes para perfiles no públicos).
- Dashboard/landing inicial (`/`).

## Responsive / UX

- Layout responsive reestructurado (commit `12ca619`, "Restructure
  responsive layout without redesign") y mejoras P1 de mobile UX
  (`ee0b5a7`), **funcionando correctamente** en mobile y desktop, sin
  cambios de diseño respecto a las fases anteriores.
- Deploy bajo `https://www.skillgames.com.ar/stickercontrol/` (ver
  `DEPLOY.md`, `DEPLOY_SKILLGAMES_REPORT.md`).

## Relación con Google Login (Fase 2A)

Esta es la versión **inmediatamente anterior** a
`v1.0-google-login-beta` (commit "StickerControl 2026 - Fase 2A Google
Login multiusuario"). A partir de esa versión, la app requiere login con
Google y cada usuario tiene su propia colección. Ver
`GOOGLE_LOGIN_IMPLEMENTATION_REPORT.md` y
`GOOGLE_LOGIN_DEPLOY_CHECKPOINT.md` para el detalle de esos cambios y el
procedimiento de deploy/rollback.

## Instrucciones de rollback a esta versión

En el VPS, dentro de `/var/www/skillgames/stickercontrol-2026`:

```bash
git fetch origin
git checkout v0.9-single-user-stable

# Backend
cd backend
source .venv/bin/activate
pip install -r requirements.txt   # por si difieren versiones de dependencias
cd ..

# Frontend
cd frontend
npm install
npm run build
cd ..

# Reiniciar servicios
systemctl restart stickercontrol-backend
systemctl reload nginx
```

Notas:
- La base de datos (`backend/stickercontrol.db`) **no se modifica** por este
  rollback de código. Si la Fase 2A ya aplicó la migración de `google_id`
  (columna nueva + índice único en `users`), esa migración es aditiva y no
  rompe el código de `v0.9` (las columnas extra simplemente no se usan). No
  es necesario restaurar el `.db` desde backup para volver a `v0.9`, salvo
  que se quiera deshacer también los datos creados durante la prueba de
  Google Login.
- Tras el `checkout`, el repo queda en estado "detached HEAD" sobre el tag.
  Para volver a trabajar sobre `main`: `git checkout main`.
