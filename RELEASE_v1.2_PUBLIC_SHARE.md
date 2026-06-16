# RELEASE v1.2 — Public Share Read-Only Link
**Fecha:** 2026-06-16  
**Tag:** `v1.2-public-share`  
**Branch:** `main`  
**Base:** v1.1-jpn-group-order

---

## Funcionalidades agregadas

### Link público de solo lectura (Fase 2B)

Un usuario logueado puede generar una URL única que permite a cualquier visitante ver su álbum, faltantes y repetidas **sin login y sin poder editar**.

**Flujo de usuario:**
1. Usuario abre Dashboard → sección "Compartir mi álbum"
2. Primera vez: botón "Generar link público" → genera token una sola vez (idempotente)
3. Siguiente visita: el Dashboard recupera y muestra el link automáticamente al recargar
4. Visitante abre `https://dominio/stickercontrol/share/<token>` sin necesidad de cuenta
5. Ve progreso del álbum (%), pestañas Álbum / Faltantes / Repetidas
6. Puede copiar faltantes y repetidas para WhatsApp
7. No puede hacer ninguna acción de edición (badges son `<div>`, no `<button>`)

**Privacidad garantizada:**
- Notas personales: nunca expuestas (`model_copy(update={"notes": None})` en cada sticker)
- Email del propietario: nunca expuesto (endpoint devuelve solo `owner_name`)
- Token: 128 bits de entropía (`secrets.token_urlsafe(16)`), no enumerable

---

## Archivos modificados

### Backend (5 archivos)

| Archivo | Tipo | Descripción del cambio |
|---|---|---|
| `backend/app/models.py` | Modificado | `share_token: Mapped[str \| None]` en clase `User` |
| `backend/app/database.py` | Modificado | `_ensure_share_token_column()` — migración idempotente en startup |
| `backend/app/schemas.py` | Modificado | `ShareTokenResponse`, `PublicOwnerResponse` |
| `backend/app/routes/share.py` | **Nuevo** | Router con 6 endpoints (2 auth + 4 públicos) |
| `backend/app/main.py` | Modificado | `app.include_router(share.router)` |

### Frontend (4 archivos)

| Archivo | Tipo | Descripción del cambio |
|---|---|---|
| `frontend/src/api/client.js` | Modificado | `generateShareToken`, `getShareToken`, `getPublicOwner/Album/Missing/Duplicates` |
| `frontend/src/App.jsx` | Modificado | `<Route path="/share/:token">` fuera de `PrivateRoute` |
| `frontend/src/pages/ShareView.jsx` | **Nuevo** | Vista pública con tabs, ProgressRing, botones WhatsApp |
| `frontend/src/pages/Dashboard.jsx` | Modificado | Sección "Compartir mi álbum" con recuperación de token al recargar |

### Documentación (incluida en este commit)

| Archivo | Descripción |
|---|---|
| `PUBLIC_SHARE_READONLY_AUDIT.md` | Auditoría de diseño pre-implementación |
| `RELEASE_v1.2_PUBLIC_SHARE.md` | Este archivo |

> Los archivos `PUBLIC_SHARE_READONLY_IMPLEMENTATION_REPORT.md` y `PRE_DEPLOY_AUDIT_FASE_2B.md`
> se encuentran en el directorio padre (`../`) fuera del repositorio.

---

## Endpoints nuevos

### Autenticados (requieren sesión)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/share/generate` | Genera token (idempotente) |
| `GET` | `/api/share/token` | Recupera token actual (`null` si sin token) |

### Públicos (sin sesión)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/public/{token}` | Nombre del propietario |
| `GET` | `/api/public/{token}/album` | Álbum completo (sin notes) |
| `GET` | `/api/public/{token}/missing` | Faltantes + texto WhatsApp |
| `GET` | `/api/public/{token}/duplicates` | Repetidas + texto WhatsApp |

Token inválido → `HTTP 404`.

---

## Migraciones realizadas

### Local (ya aplicada)
```sql
-- Ejecutada automáticamente en startup via database.py:
ALTER TABLE users ADD COLUMN share_token VARCHAR;
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_share_token ON users (share_token);
```
Migración idempotente — segura de correr múltiples veces.

### VPS (PENDIENTE — acción obligatoria antes de deploy)
La migración de `share_token` se aplica **automáticamente** al reiniciar uvicorn en el VPS. No requiere SQL manual.

La migración **JAP→JPN** en cambio SÍ requiere SQL manual en la DB de producción (ver sección Riesgos).

---

## Riesgos conocidos

### CRÍTICO — JAP→JPN no aplicado en VPS
La corrección de Japón (v1.1) fue aplicada en local pero **no en el VPS**. El álbum público mostraría `JAP` para Japón si no se aplica el SQL antes del deploy.

**SQL a ejecutar en VPS antes de deploy:**
```bash
# Backup obligatorio
cp stickercontrol.db stickercontrol.db.bak-predeploy-$(date +%Y%m%d-%H%M%S)

# Corrección
sqlite3 stickercontrol.db <<'EOF'
UPDATE master_stickers SET code = 'JPN' || substr(code, 4) WHERE country_code = 'JAP';
UPDATE master_stickers SET country_code = 'JPN' WHERE country_code = 'JAP';
EOF

# Verificación
sqlite3 stickercontrol.db "SELECT COUNT(*) FROM master_stickers WHERE country_code = 'JPN';"
# Debe devolver: 20
```

Ver detalle completo en `CORRECTION_REPORT_GROUPS_JPN.md §8`.

### MENOR — Token no revocable
Una vez generado el `share_token`, el usuario no puede revocarlo desde la UI. Para desactivar un link hay que poner `share_token = NULL` manualmente en DB.

### MENOR — Sin rate limiting en endpoints públicos
Los endpoints `/api/public/{token}/*` no tienen throttling. El token de 128 bits hace la enumeración computacionalmente inviable, pero scraping masivo de un álbum conocido es posible.

---

## Checklist de deploy en VPS

### Pre-deploy
- [ ] **CRÍTICO** Backup de DB: `cp stickercontrol.db stickercontrol.db.bak-v1.2-$(date +%Y%m%d)`
- [ ] **CRÍTICO** Aplicar SQL JAP→JPN en DB de producción (ver arriba)
- [ ] Verificar que el flag `JPN.png` existe en `/var/www/stickercontrol/flags/` (o la ruta equivalente)
- [ ] `git pull origin main` en el servidor

### Deploy backend
- [ ] Copiar/sincronizar `backend/` al VPS
- [ ] `sudo systemctl restart stickercontrol` (o el nombre del servicio uvicorn)
- [ ] Verificar log de startup: `journalctl -u stickercontrol -n 20`
- [ ] Confirmar que aparece `Application startup complete.` sin errores
- [ ] Verificar migración automática: `PRAGMA table_info(users)` debe incluir `share_token`

### Deploy frontend
- [ ] Ejecutar `npm run build` en local (o en el servidor)
- [ ] Copiar `frontend/dist/` al directorio servido por nginx
- [ ] Verificar que `index.html` y assets actualizados están en el servidor

### Post-deploy verificación
- [ ] `GET https://dominio/stickercontrol/api/` → `{"status": "ok"}`
- [ ] Login Google funciona
- [ ] Álbum privado carga con JPN en lugar de JAP
- [ ] Dashboard muestra sección "Compartir mi álbum"
- [ ] Generar link → URL aparece
- [ ] Abrir link en ventana incógnita → vista pública carga sin login
- [ ] Tab Faltantes → botón "Copiar para WhatsApp" funciona
- [ ] Tab Repetidas → botón "Copiar para WhatsApp" funciona
- [ ] URL inválida → página "Álbum no encontrado"

---

## Rollback

Si es necesario revertir a v1.1:

```bash
git checkout v1.1-jpn-group-order
npm run build
# Copiar dist/ al servidor
sudo systemctl restart stickercontrol
```

La columna `share_token` permanece en la DB (no causa problemas en v1.1 — columna ignorada).

---

## Historial de versiones

| Tag | Descripción |
|---|---|
| `v0.9-single-user-stable` | Single-user sin auth |
| `v1.0-google-login-beta` | Google Login multiusuario (Fase 2A) |
| `v1.1-jpn-group-order` | Fix JAP→JPN + orden oficial grupos H/I/L |
| `v1.2-public-share` | **Esta versión** — link público solo lectura (Fase 2B) |
