# TODO / Roadmap

## Fase 0 — MVP local funcional

- [x] Estructura del proyecto (backend + frontend independientes)
- [x] Sync de `countries.json` y banderas desde el proyecto padre
- [x] Base SQLite + modelos (`users`, `master_stickers`, `user_stickers`)
- [x] `master_stickers` vacía + `seed_db.py` con dataset de prueba (4 países + FWC)
- [x] Lógica de estado (`FALTANTE` / `DISPONIBLE_PARA_PEGAR` /
      `PEGADA_SIN_REPETIDA` / `PEGADA_CON_REPETIDA`) + repetidas
- [x] `GET /api/stickers/search`
- [x] Acciones de colección: pegar/despegar, +1/-1, marcar faltante, notas
- [x] `GET /api/reports/album` (agrupado A-L + especiales)
- [x] `GET /api/reports/missing` + texto WhatsApp
- [x] `GET /api/reports/duplicates` + texto WhatsApp
- [x] Router `trades` placeholder (sin lógica)
- [x] Frontend: Dashboard, Buscar, Álbum, Faltantes, Repetidas, Intercambios ("Próximamente")
- [x] Verificación end-to-end (backend + frontend corriendo juntos)

## Fase 0.5 — Catálogo real (nombres genéricos)

- [x] `scripts/import_master_stickers_from_xlsm.py`: lee
      `docs/StickerAlbumWC2026.xlsm` (hoja "Stickers") y genera
      `data/stickers_master.csv`
- [x] Reemplazar `data/stickers_master.csv` (dataset de prueba, 85 filas)
      por el catálogo real (980 figuritas: 48 países x 20 + 19 especiales
      FIFA + 1 logo/portada código `00`)
- [x] `player_name_or_detail` genérico derivado del código (`MEX1 ->
      "Mexico 1"`, `FWC1 -> "Especial FIFA 1"`) — sin jugadores reales
- [x] `seed_db.py`: upsert por `code` + eliminar códigos que ya no estén en el CSV
- [x] Verificar `/api/stickers/search?q=MEX1`, `?q=ARG10` y `/api/reports/album`
      con el catálogo real
- [x] `IMPORT_MASTER_STICKERS_REPORT.md` con detalle de la importación
- [ ] Enriquecer `player_name_or_detail` con jugadores reales, una vez
      confirmada la fuente oficial definitiva (fase futura, no planificada
      todavía)

## Fase 0.6 — Usuarios cerca (MVP de intercambio sin chat)

- [x] Columnas de perfil público en `users` (`display_name`, `city`,
      `latitude`, `longitude`, `contact_email`, `contact_whatsapp`,
      `is_public`) + migración liviana (`_ensure_user_profile_columns`)
- [x] `app/geo.py`: `haversine_km()` + `round_coord()` (privacidad: no se
      guarda ubicación exacta)
- [x] `GET`/`PATCH /api/profile`
- [x] `GET /api/nearby` (coincidencias + distancia aproximada, ordenado por
      `match_count` y `distance_km`)
- [x] `GET /api/nearby/{user_id}/contact-message`
- [x] Frontend: página `/cerca` (perfil + tarjetas de coleccionistas
      cercanos, Copiar mensaje / WhatsApp / Email)
- [x] Verificación end-to-end (backend + frontend) con base temporal
- [x] [`NEARBY_USERS_MVP.md`](./NEARBY_USERS_MVP.md): alcance, privacidad,
      limitaciones, por qué no hay chat interno

> **Decisión de producto**: no se implementa chat interno, solicitudes de
> intercambio, mensajería, notificaciones, moderación, WebSockets ni
> Firebase. No es un pendiente — ver `NEARBY_USERS_MVP.md`.

## Fase 0.6.1 — Auditoría forense de Usuarios cerca

- [x] Entorno aislado con base SQLite temporal y 9 usuarios de prueba
- [x] Validar distancias, `match_count`, intercambio bidireccional,
      ordenamiento, mensajes, links y casos límite
- [x] [`NEARBY_FORENSIC_TEST.md`](./NEARBY_FORENSIC_TEST.md): bug B1
      (`contact-message` no valida `is_public`) + riesgos R1-R4

## Fase 0.6.2 — Preparación para deploy bajo SkillGames

- [x] Corregir bug B1: `GET /api/nearby/{user_id}/contact-message` devuelve
      `404` si el usuario no existe o no es público (mismo mensaje en
      ambos casos)
- [x] `/api/nearby` ya no expone `contact_email`/`contact_whatsapp` en texto
      plano (`has_email`/`has_whatsapp`); `contact-message` genera
      `whatsapp_url`/`mailto_url` en el servidor
- [x] `vite.config.js`: `base` condicional (`/stickercontrol/` en
      producción, `/` en desarrollo)
- [x] `main.jsx`: `basename` de `BrowserRouter` desde
      `import.meta.env.BASE_URL`
- [x] `client.js`: `BASE_URL` dinámico (`/api` en dev,
      `/stickercontrol/api` en producción); `Nearby.jsx` usa
      `has_email`/`has_whatsapp` + `whatsapp_url`/`mailto_url`
- [x] Landing en `Dashboard.jsx` ("Controlá tus figuritas del Mundial 2026",
      bullets, botón "Empezar")
- [x] `DEPLOY.md` con ejemplo real de nginx (`/stickercontrol/` +
      `/stickercontrol/api/`), systemd, ubicación de SQLite y backup
- [x] `npm run build`, `npm run preview` y `npm run dev` verificados;
      rutas `/stickercontrol`, `/stickercontrol/cerca`,
      `/stickercontrol/faltantes` documentadas
- [x] [`DEPLOY_SKILLGAMES_REPORT.md`](./DEPLOY_SKILLGAMES_REPORT.md) con el
      detalle de cambios y pruebas

> Alcance respetado: sin login, chat, OAuth ni invitaciones en esta fase.

## Fase 1 — Login Google + multi-usuario

- [ ] Implementar Google OAuth (login)
- [ ] Reemplazar `get_current_user_id()` (hoy devuelve `1` fijo) por la
      sesión real del usuario autenticado, sin tocar las rutas existentes
- [ ] Migrar la colección del usuario local (`id=1`) al primer usuario real
      que inicie sesión (o dejarla como "colección demo")
- [ ] Manejo de sesiones (cookies/JWT) y variables de entorno para
      `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`

## Fase 2 — Intercambios

- [ ] Implementar lógica en `routes/trades.py`: parsear listas
      "ofrece"/"necesita" de otro coleccionista
- [ ] Cruzar contra faltantes/repetidas del usuario actual
- [ ] Calcular balance del intercambio
- [ ] Generar texto listo para WhatsApp

## Fase 3 — Export/backup + deploy

- [ ] Export/backup de la base de datos (descarga de SQLite o export CSV)
- [ ] Deploy en VPS Ubuntu (ver [`DEPLOY.md`](./DEPLOY.md))
