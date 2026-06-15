# Checkpoint pre-deploy — StickerControl 2026

## Datos del checkpoint

- **Fecha**: 2026-06-15
- **Branch**: `main`
- **Commit**: `a8dee1e197de8b36b208617d08b169f1ccb13c19`
  - Mensaje: `StickerControl 2026 - Beta pre-deploy estable`
  - Commit raíz (primer commit del repo, 115 archivos).
- **Tag**: `v0.9-beta-predeploy` (anotado, pusheado a `origin`)
- **Remoto**: `https://github.com/Playcool32/stickercontrol-2026`

## Catálogo de figuritas

- **Total**: 980 figuritas (`data/stickers_master.csv` / `master_stickers`)
- **Selecciones**: 48 (12 grupos A-L x 4 países x 20 figuritas cada uno)
- **Especiales**: 20 (`00` logo oficial + `FWC1`-`FWC19`)

## Estado de build / servidores

- **Build frontend**: OK — `npm run build` → `✓ 51 modules transformed`,
  `dist/` generado sin errores.
- **Backend**: corriendo (`uvicorn app.main:app --reload --port 8000`),
  `GET /` → `200`.
- **Frontend**: corriendo (`npm run dev`, puerto 5173), `GET /` → `200`.

## Funcionalidades implementadas

- Catálogo real completo (980 figuritas: 48 selecciones + 20 especiales FWC,
  códigos `FWC1`-`FWC19` + `00`).
- Buscador (`/buscar`): caja de búsqueda mínima, sin resultados iniciales,
  debounce + mínimo 2 caracteres (excepto `00`), máximo 10 resultados.
- Álbum (`/album`): grilla por grupo A-L + sección "Especiales del Mundial"
  (orden real del sorteo FIFA por grupo), resumen por país (pegadas/
  faltantes/repetidas/%), modal de detalle de figurita reutilizando
  `StickerCard` (Pegar/Despegar, +1/-1, Marcar faltante, notas).
- Acciones de colección: pegar/despegar, +1/-1, marcar faltante, notas —
  persistencia inmediata vía `/api/collection/*`.
- Reportes Faltantes/Repetidas (`/faltantes`, `/repetidas`) con texto listo
  para WhatsApp.
- "Usuarios cerca" (`/cerca`): perfil público, distancia aproximada,
  coincidencias de intercambio (faltantes/repetidas cruzadas), mensaje de
  contacto (WhatsApp/email) sin exponer datos de contacto en texto plano.
- Router `trades` (Intercambios): placeholder "Próximamente", sin lógica.
- Preparado para deploy bajo subpath `/stickercontrol/` (base de Vite,
  `BrowserRouter` basename, `client.js` `BASE_URL` dinámico) — ver
  `DEPLOY.md` / `DEPLOY_SKILLGAMES_REPORT.md`.

## Pendientes para post-deploy

- **Fase 1**: login Google OAuth + multi-usuario (reemplazar
  `get_current_user_id()` fijo en `1`, migración de la colección local).
- **Fase 2**: lógica real de Intercambios (`routes/trades.py`).
- **Fase 3**: export/backup de la base SQLite y deploy en VPS (ver
  `DEPLOY.md`).
- Enriquecer `player_name_or_detail` con nombres de jugadores reales cuando
  se confirme la fuente oficial (hoy es genérico: `MEX1 -> "Mexico 1"`,
  `FWC1 -> "Especial FIFA 1"`).
- Guardado diferido en `StickerCard` (Pegar/+1/-1/Marcar faltante como
  borrador local + botón Guardar) — auditado en `DEFERRED_SAVE_AUDIT.md`,
  no implementado; requiere decisiones de producto antes de implementar.

## Restricciones respetadas en este checkpoint

- No se modificó código, configuración, diseño ni base de datos
  (`backend/*.db` está en `.gitignore`, no se versionó).
- Solo se ejecutaron: `git init`, `git add`, `git commit`, `git remote add`,
  `git push`, `git tag`, `git push --tags` y este informe.
