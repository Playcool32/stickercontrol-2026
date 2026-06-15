# Usuarios cerca — MVP de intercambio (Fase 0.6)

## Decisión de producto

La app va a usarse intensamente durante pocos días/semanas (el Mundial
2026) y después prácticamente deja de usarse. Por eso se descartó construir
una red social: **no hay chat interno, no hay solicitudes de intercambio,
no hay mensajería dentro de la app, no hay notificaciones, no hay
moderación, no hay WebSockets ni Firebase**.

En cambio, "Usuarios cerca" es una función mínima: ayuda a encontrar otros
coleccionistas cercanos con los que **podrías** intercambiar, calcula las
coincidencias (qué le falta a cada uno) y genera un mensaje de texto listo
para enviar. El intercambio real (coordinar dónde, cuándo, etc.) sucede
**fuera de la app**, por WhatsApp o email.

## Alcance

- **Perfil público opcional** (`GET`/`PATCH /api/profile`): cada usuario
  puede agregar `display_name`, `city`, una ubicación aproximada
  (`latitude`/`longitude`), `contact_email`, `contact_whatsapp` y un flag
  `is_public`. Por defecto `is_public=false` — el usuario tiene que activarlo
  explícitamente para aparecer en los listados de otros.
- **`GET /api/nearby`**: devuelve los usuarios públicos (`is_public=true`,
  excepto uno mismo), con `display_name`, `city`, `distance_km` aproximada,
  las figuritas que a mí me faltan y el otro tiene repetidas
  (`stickers_i_need_that_user_has`), las figuritas que al otro le faltan y yo
  tengo repetidas (`stickers_user_needs_that_i_have`) y `match_count` (suma
  de ambas listas). Ordenado por mayor `match_count` y luego menor
  `distance_km`.
- **`GET /api/nearby/{user_id}/contact-message`**: genera el texto de
  contacto ("Hola, soy ... A mí me interesan: ... Yo tengo repetidas que
  quizás te sirven: ... ¿Te interesa coordinar?"), listo para copiar, mandar
  por WhatsApp (`https://wa.me/<numero>?text=...`) o por email
  (`mailto:...?subject=...&body=...`).
- **Frontend** (`/cerca`, página "Usuarios cerca"): formulario para editar el
  propio perfil (incluye botón "Usar mi ubicación" con
  `navigator.geolocation`) + tarjetas de coleccionistas cercanos con botones
  "Copiar mensaje", "Contactar por WhatsApp" y "Contactar por email".

## Privacidad

- **`is_public` es opt-in** (`false` por defecto): nadie aparece en `/api/nearby`
  a menos que active explícitamente "Mostrarme a otros coleccionistas
  cercanos".
- **No se guarda la dirección exacta**: las coordenadas se redondean a 2
  decimales (~1.1 km de resolución) antes de guardarse en `PATCH /api/profile`
  (`app/geo.py::round_coord`).
- **Email y WhatsApp no se muestran como texto en los listados**: `/api/nearby`
  los incluye en la respuesta solo para que el frontend construya los enlaces
  `wa.me`/`mailto` de los botones de contacto; la tarjeta de cada usuario
  muestra únicamente nombre, ciudad, distancia aproximada y coincidencias.
- El contacto real (decidir dónde y cuándo encontrarse) ocurre **fuera de la
  app**, por WhatsApp o email — la app no guarda ni intermedia esa
  conversación.

## Limitaciones conocidas (aceptadas para este MVP)

- La distancia es aproximada (haversine entre coordenadas redondeadas), no
  hay mapa ni geocodificación de direcciones.
- No hay verificación de que el contacto provisto (`contact_email` /
  `contact_whatsapp`) sea válido o esté activo.
- No hay forma de bloquear/reportar usuarios ni de ocultarse de alguien en
  particular — solo el on/off global `is_public`.
- Las coincidencias se recalculan en cada request (no hay caché ni
  notificación de "nuevas coincidencias").
- Pensado para single-user local (Fase 0): el "yo" siempre es el usuario
  `id=1` (`get_current_user_id()`), igual que el resto de la app hasta que
  llegue el login real (Fase 1).

## Por qué no hay chat interno

Construir chat, solicitudes de intercambio, notificaciones y moderación
implica mucho desarrollo y mantenimiento (WebSockets, persistencia de
mensajes, spam/abuso, etc.) para una app que se usa intensamente durante
días y luego queda en desuso. WhatsApp y el email ya resuelven la
comunicación de forma confiable y sin trabajo adicional — la app solo tiene
que ayudar a **encontrar** con quién hablar y **qué** decirle.
