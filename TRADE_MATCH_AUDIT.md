# Auditoría — Intercambios básicos entre coleccionistas (Fase 2D)

## 1. Qué ya existe

- **`crud.get_missing_and_duplicate_codes(db, user_id)`** (`backend/app/crud.py:47`) ya calcula, para cualquier usuario, el set de códigos `FALTANTE` y el set de códigos con `repetidas>0`. Es exactamente el insumo que necesita un cruce de intercambio.
- **`routes/nearby.py`** (`GET /api/nearby`) ya hace el cruce completo entre "yo" y cada usuario público: `stickers_i_need_that_user_has = my_missing & other_duplicates` y `stickers_user_needs_that_i_have = other_missing & my_duplicates` (`nearby.py:51-52`). Esto **es** el algoritmo de intercambio pedido — hoy se calcula pero solo se expone como conteo (`match_count`) en la lista de cercanos, no como un detalle dedicado por usuario.
- **`routes/nearby.py` → `GET /api/nearby/{other_user_id}/contact-message`** ya tiene el patrón exacto de seguridad a reutilizar: valida `other.is_public`, devuelve 404 genérico si no existe o no es público, y genera un texto + `whatsapp_url`/`mailto_url` en el servidor (nunca expone el email/whatsapp en texto plano al cliente salvo dentro de la URL ya armada).
- **`routes/trades.py`** es un placeholder puro: `GET /api/trades/status` → `{"implemented": false}`. Ya está registrado en `main.py` (`app.include_router(trades.router)`), así que agregar un endpoint nuevo ahí no requiere tocar `main.py`.
- **`schemas.py`**: no hay ningún schema de "trade" todavía. Sí existen `NearbyUser`/`NearbyResponse`/`ContactMessageResponse`, que son el modelo a imitar.
- **`reports.py` / `share.py`**: no tienen nada relacionado a intercambios; solo se usan como fuente de lectura (`_all_stickers_with_status`) y no hace falta tocarlos para el caso 1 (Usuarios cerca). Para el caso 2 (vía link público) sí serían relevantes, ver sección 8.
- **`models.py`**: no tiene tabla de "solicitudes" ni de "intercambios" — no existe ningún estado persistente de trades, lo cual es coherente con la restricción de no implementar solicitudes/historial.
- **Frontend**: `Trades.jsx` es 100% placeholder ("Próximamente"), ya enrutado en `/intercambios` (`App.jsx:41`). `Nearby.jsx` ya tiene el patrón completo de "calcular algo on-demand por usuario + cachear en estado + copiar/WhatsApp" vía `getContactMessage`/`handleCopy`/`handleWhatsapp` — es el mismo patrón a reutilizar para "Calcular intercambio".

## 2. Qué falta

- Un endpoint que, dado un `other_user_id` puntual, devuelva el detalle de intercambio (hoy solo existe agregado dentro de la lista completa de `/api/nearby`, sin un "detalle por usuario" reutilizable fuera de esa lista).
- Información enriquecida de cada código (país, número) para mostrar tarjetas legibles — hoy `stickers_i_need_that_user_has` son solo strings de código (`"ARG10"`), suficiente para texto pero no para una tarjeta visual con bandera/nombre si se quisiera más adelante (fuera de alcance del MVP, ver decisión en sección 8).
- Texto de resumen ya armado en el servidor (mismo patrón que `contact-message`) para el botón "Copiar resumen para WhatsApp".
- Activar `Trades.jsx` con contenido real: la pantalla "Intercambios" debe dejar de ser un placeholder.
- Botón "Calcular intercambio" en cada tarjeta de `Nearby.jsx`.

## 3. Endpoint recomendado

```
GET /api/trades/with-user/{other_user_id}
```

- Requiere sesión (`get_current_user_id`).
- Solo lectura: no escribe en `user_stickers` ni en ninguna tabla.
- Valida `other_user_id != user_id` (400 si es uno mismo) y `other.is_public == True` (404 si no existe o no es público — mismo criterio que `contact-message`, mismo mensaje genérico para no filtrar si el id existe pero es privado).
- Responde:

```json
{
  "other_user": { "user_id": 7, "display_name": "Lu", "city": "Rosario" },
  "i_can_give": ["ARG10", "BRA4", "ESP7"],
  "i_can_receive": ["MEX3", "JPN12"],
  "summary_text": "Intercambio con Lu:\n\nYo puedo darte: ARG10, BRA4, ESP7\nVos podés darme: MEX3, JPN12\n\n¿Coordinamos?"
}
```

`other_user` deliberadamente no incluye `contact_email`/`contact_whatsapp`/`latitude`/`longitude` — ese contacto ya tiene su propio endpoint (`/api/nearby/{id}/contact-message`) y no hace falta duplicarlo aquí. El botón "Copiar resumen para WhatsApp" del MVP copia `summary_text` al portapapeles (mismo patrón `navigator.clipboard.writeText` que ya usa `Nearby.jsx`), no genera un link `wa.me` nuevo — si el usuario quiere mandarlo por WhatsApp ya tiene el botón de WhatsApp existente en la tarjeta de "Usuarios cerca" para abrir la conversación.

## 4. Algoritmo de cruce

Idéntico al ya implementado en `/api/nearby`, solo que evaluado para un único `other_user_id` en lugar de para todos los usuarios públicos:

```python
my_missing, my_duplicates = get_missing_and_duplicate_codes(db, user_id)
other_missing, other_duplicates = get_missing_and_duplicate_codes(db, other_user_id)

i_can_give = sorted(my_duplicates & other_missing)      # mis repetidas que a el le faltan
i_can_receive = sorted(other_duplicates & my_missing)    # sus repetidas que a mi me faltan
```

Nota de nombres: lo que `nearby.py` llama `stickers_i_need_that_user_has` es matemáticamente igual a `i_can_receive` aquí (sus repetidas cruzadas con mis faltantes), y `stickers_user_needs_that_i_have` es igual a `i_can_give`. Mismo cálculo, nombre adaptado al lenguaje de "intercambio" pedido en el spec.

Se basa en `quantity`/`is_pasted` ya persistidos (vía `compute_status`/`compute_repetidas` de `status.py`), sin tocar `user_stickers` ni `master_stickers`: 100% lectura.

## 5. Riesgos de privacidad

- **Igual que en `nearby.py`**: solo se puede calcular intercambio contra un usuario con `is_public=True`. Sin esto, sería posible enumerar la colección de cualquier usuario por id — riesgo ya mitigado en el patrón existente, hay que replicarlo exactamente (404 genérico, no 403, para no confirmar si el id existe).
- **No exponer `notes`**: el endpoint nunca toca `notes`, solo trabaja con códigos (`get_missing_and_duplicate_codes` no las devuelve).
- **No exponer email/whatsapp/ubicación exacta**: `other_user` en la respuesta se limita a `user_id`, `display_name`, `city` (mismos campos no sensibles que ya expone `NearbyUser`). La ubicación nunca fue exacta desde Fase 0.6 (`round_coord`), y aquí ni siquiera se incluye distancia.
- **Auto-intercambio**: bloquear explícitamente `other_user_id == user_id` (sin esto, alguien podría "intercambiar contra sí mismo" sin sentido funcional, aunque no sería un riesgo de seguridad, sí un caso confuso a evitar con un 400 claro).
- **Sin nuevo estado persistente**: como no hay tabla de "solicitudes", no hay riesgo de fuga de historial de intercambios entre usuarios — cada cálculo es efímero y se descarta al cerrar la pantalla.

## 6. Archivos a tocar (si se aprueba la implementación)

- `backend/app/schemas.py` — nuevos schemas `TradeOtherUser`, `TradeMatchResponse`.
- `backend/app/routes/trades.py` — nuevo endpoint `GET /api/trades/with-user/{other_user_id}`, reutilizando `get_missing_and_duplicate_codes` de `crud.py` (sin tocar `crud.py`, la función ya sirve tal cual).
- `frontend/src/api/client.js` — nueva función `getTradeMatch(otherUserId)`.
- `frontend/src/pages/Nearby.jsx` — botón "Calcular intercambio" por tarjeta (mismo patrón on-demand + cache en estado que `getContactMessage`), con un panel inline mostrando `i_can_give`/`i_can_receive` y botón "Copiar resumen".
- `frontend/src/pages/Trades.jsx` — deja de ser "Próximamente": lista los mismos usuarios públicos de `/api/nearby` (reutilizando `getNearby()`) con la misma acción "Calcular intercambio", para que la pantalla "Intercambios" tenga contenido real sin duplicar la edición de perfil (que sigue viviendo solo en `Nearby.jsx`).

No hace falta tocar: `models.py`, `database.py`, `crud.py`, `main.py` (el router de `trades` ya está incluido), `reports.py`, `share.py`, `auth.py`, esquema de DB.

## 7. Estimación

**Baja-media.** ~2-3 horas: un endpoint backend reutilizando una función ya existente y probada (`get_missing_and_duplicate_codes`), dos schemas nuevos, una función de cliente, y la parte más laboriosa es frontend (un botón + panel inline en `Nearby.jsx`, y convertir `Trades.jsx` de placeholder a una vista funcional reutilizando el mismo fetch que `Nearby`). Sin migración de DB, sin dependencias nuevas.

## 8. Decisión: ¿solo desde Usuarios cerca, o también desde share link?

**Implementar primero y únicamente el caso 1 (Usuarios cerca). Documentar el caso 2 (comparar contra un link público) como Fase 2D.2, sin implementarlo ahora.**

Motivos:
- El caso 1 reutiliza 100% el patrón de seguridad y datos que ya existe (`is_public`, usuarios autenticados entre sí). Es una extensión natural y de bajo riesgo de lo que ya está en producción.
- El caso 2 introduce una pregunta de producto sin resolver todavía: ¿quién es "yo" al comparar contra un link público? El visitante del link público hoy es siempre anónimo (sin sesión) — para poder cruzar "mi colección" contra ese álbum, habría que o bien (a) requerir que el visitante esté logueado igual y combinar sesión autenticada + token público en el mismo flujo (cambia el modelo mental de "el link público es de solo lectura, sin login"), o (b) calcular el cruce completamente en el cliente combinando `/api/public/{token}/missing` + `/api/public/{token}/duplicates` (públicos, ya existen) contra los propios `/api/reports/missing|duplicates` del usuario logueado, sin necesidad de un endpoint backend nuevo. La opción (b) es técnicamente simple y no requeriría tocar `share.py`, pero mezclar esa lógica en el mismo MVP agrega superficie de prueba (¿qué pasa si el token es de uno mismo? ¿se valida que el visitante esté logueado para ver ese botón?) que no aporta al caso de uso principal pedido (Usuarios cerca).
- Mantener el primer entregable chico y probado reduce el riesgo de romper producción, en línea con la prioridad indicada ("simple, reversible y sin romper producción").

## 9. Conclusión de la auditoría

**Riesgo bajo.** El endpoint propuesto no introduce datos nuevos, reutiliza lógica ya verificada en producción (`/api/nearby`), no requiere migración, y replica exactamente los controles de privacidad ya existentes. Recomendado proceder a implementar el MVP del caso 1 (Usuarios cerca) tal como está diseñado en las secciones 3, 4 y 6, dejando el caso 2 (share link) documentado para una fase posterior.
