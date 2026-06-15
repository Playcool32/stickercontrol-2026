# Auditoría forense — Fase 0.6.1: "Usuarios cerca"

> **Tipo de documento**: auditoría/validación. No se modificó código de la
> aplicación (`backend/app/**` sin cambios). Los únicos archivos creados
> fueron un script de seeding temporal y una base SQLite temporal, ambos
> borrados al finalizar.

## 1. Metodología

1. Se creó una base SQLite **independiente y temporal**
   (`backend/_forensic_test.db`, vía `DATABASE_URL` override — el mismo
   patrón usado en las verificaciones de Fase 0/0.5/0.6), sin tocar
   `backend/stickercontrol.db`.
2. Se sembraron **9 usuarios** con un catálogo de prueba de **11 códigos**
   reales del álbum (`ARG10, ARG11, ARG1, BRA5, MEX3, ESP7, FRA2, GER4, JAP6,
   CAN8, CAN1`), diseñados a propósito para cubrir:
   - Coincidencias **altas, medias, bajas y nulas**.
   - Distancias **<2 km, <10 km y >100 km**, y un caso **sin ubicación**.
   - Los edge cases pedidos: sin email, sin WhatsApp, perfil privado, sin
     repetidas, sin faltantes, coordenadas nulas.
3. Se levantó el backend (`uvicorn`) apuntando a esa base temporal en el
   puerto `8124` y se golpeó la API real con `curl` (no mocks, no
   `TestClient`).
4. Se midió tiempo de respuesta con `curl -w "%{time_total}"`.
5. Se verificó el armado de enlaces `wa.me`/`mailto` con
   `urllib.parse.quote` (equivalente a `encodeURIComponent`, que es lo que
   usa `Nearby.jsx`).
6. Al finalizar se borraron el script de seeding y la base temporal.

## 2. Usuarios simulados

| ID | display_name      | Ciudad                          | lat,lon          | is_public | email | whatsapp |
|----|--------------------|----------------------------------|-------------------|-----------|-------|----------|
| 1  | Fer (yo)           | Buenos Aires (CABA)               | -34.60, -58.38    | true      | sí    | sí       |
| 2  | Vecino B           | Buenos Aires (CABA) - Vecino      | -34.61, -58.39    | true      | sí    | sí       |
| 3  | Conocido C         | Avellaneda                        | -34.66, -58.43    | true      | sí    | sí       |
| 4  | Lejano D           | Mar del Plata                     | -38.01, -57.54    | true      | **no**| sí       |
| 5  | Sin Match E        | Córdoba                           | -31.42, -64.19    | true      | sí    | **no**   |
| 6  | Privado F          | Buenos Aires (CABA) - Privado     | -34.60, -58.39    | **false** | sí    | sí       |
| 7  | Sin Ubicación G    | Ubicación no compartida           | **null, null**    | true      | sí    | sí       |
| 8  | Sin Repetidas H    | Quilmes                           | -34.64, -58.41    | true      | sí    | sí       |
| 9  | Sin Faltantes I    | San Isidro                        | -34.56, -58.34    | true      | sí    | sí       |

Estado de colección por usuario (sobre los 11 códigos del catálogo de
prueba) diseñado para que:

- **A (Fer)**: faltan `ARG10, ARG11, BRA5, MEX3, ESP7`; tiene repetidas
  `FRA2, GER4, JAP6, CAN8`.
- **B**: repetidas `ARG10, ARG11, BRA5` (cubren 3 faltantes de A); le faltan
  `FRA2, GER4, JAP6` (A las tiene repetidas) → **match alto**.
- **C**: repetida `ARG10` (1 de A); le falta `GER4` (A la tiene repetida) →
  **match medio**.
- **D**: repetida `MEX3` (1 de A); no le falta nada que A tenga → **match
  bajo (1)**, a >100 km, sin email.
- **E**: repetida `CAN1` (A no la necesita); le falta `ARG1` (A no la tiene
  repetida) → **0 coincidencias**, sin WhatsApp.
- **F**: repetidas `ARG10, ARG11, BRA5, MEX3, ESP7` (las 5 faltantes de A);
  le faltan `FRA2, GER4, JAP6, CAN8` (las 4 repetidas de A) → sería el
  **match perfecto (9)**, pero `is_public=false`.
- **G**: repetida `ARG10` (1 de A) → match=1, **sin ubicación**.
- **H**: le falta `FRA2` (A la tiene repetida) → match=1, **0 repetidas en
  todo su catálogo**.
- **I**: repetida `ARG10` (1 de A) → match=1, **0 faltantes en todo su
  catálogo**.

## 3. Distancias reales (`haversine_km`, sobre coordenadas redondeadas a 2 decimales)

| Usuario      | Distancia desde A | Bucket objetivo |
|--------------|-------------------|-----------------|
| B (Vecino)   | **1.44 km**       | < 2 km ✅       |
| C (Avellaneda)| **8.09 km**      | < 10 km ✅      |
| D (Mar del Plata) | **386.57 km** | > 100 km ✅    |
| E (Córdoba)  | 646.75 km         | (sin requisito) |
| F (privado)  | 0.92 km           | (oculto)        |
| G            | `None`            | sin ubicación ✅|
| H (Quilmes)  | 5.23 km           | < 10 km ✅      |
| I (San Isidro)| 5.76 km          | < 10 km ✅      |

`round_coord()` redondea a 2 decimales (~1.1 km de error máximo), y
`haversine_km()` calculó correctamente los 3 buckets pedidos (<2 km, <10 km,
>100 km) más el caso sin ubicación.

**Re-chequeo de `PATCH /api/profile`** (no es nuevo, pero se repitió como
parte de la auditoría): `latitude=-34.123456789` → guardado como `-34.12`;
`longitude=-58.987654321` → guardado como `-58.99`. Redondeo OK.

## 4. `GET /api/nearby` — respuesta completa (usuario 1 = Fer)

```json
{
  "users": [
    {
      "user_id": 2, "display_name": "Vecino B", "city": "Buenos Aires (CABA) - Vecino",
      "distance_km": 1.4,
      "stickers_i_need_that_user_has": ["ARG10", "ARG11", "BRA5"],
      "stickers_user_needs_that_i_have": ["FRA2", "GER4", "JAP6"],
      "match_count": 6,
      "contact_email": "b@example.com", "contact_whatsapp": "5491122223333"
    },
    {
      "user_id": 3, "display_name": "Conocido C", "city": "Avellaneda",
      "distance_km": 8.1,
      "stickers_i_need_that_user_has": ["ARG10"],
      "stickers_user_needs_that_i_have": ["GER4"],
      "match_count": 2,
      "contact_email": "c@example.com", "contact_whatsapp": "5491133334444"
    },
    {
      "user_id": 8, "display_name": "Sin Repetidas H", "city": "Quilmes",
      "distance_km": 5.2,
      "stickers_i_need_that_user_has": [],
      "stickers_user_needs_that_i_have": ["FRA2"],
      "match_count": 1,
      "contact_email": "h@example.com", "contact_whatsapp": "5491155556666"
    },
    {
      "user_id": 9, "display_name": "Sin Faltantes I", "city": "San Isidro",
      "distance_km": 5.8,
      "stickers_i_need_that_user_has": ["ARG10"],
      "stickers_user_needs_that_i_have": [],
      "match_count": 1,
      "contact_email": "i@example.com", "contact_whatsapp": "5491199990000"
    },
    {
      "user_id": 4, "display_name": "Lejano D", "city": "Mar del Plata",
      "distance_km": 386.6,
      "stickers_i_need_that_user_has": ["MEX3"],
      "stickers_user_needs_that_i_have": [],
      "match_count": 1,
      "contact_email": null, "contact_whatsapp": "5492235556666"
    },
    {
      "user_id": 7, "display_name": "Sin Ubicacion G", "city": "Ubicacion no compartida",
      "distance_km": null,
      "stickers_i_need_that_user_has": ["ARG10"],
      "stickers_user_needs_that_i_have": [],
      "match_count": 1,
      "contact_email": "g@example.com", "contact_whatsapp": "5491177778888"
    },
    {
      "user_id": 5, "display_name": "Sin Match E", "city": "Cordoba",
      "distance_km": 646.8,
      "stickers_i_need_that_user_has": [],
      "stickers_user_needs_that_i_have": [],
      "match_count": 0,
      "contact_email": "e@example.com", "contact_whatsapp": null
    }
  ]
}
```

**Usuario 6 (Privado F) NO aparece** — correcto, pese a tener el match más
alto posible (9).

## 5. Validación de `match_count` (sección 3 del pedido)

| Usuario | repetidas que sirven a A | faltantes que A cubre | match_count |
|---------|---------------------------|------------------------|-------------|
| B       | ARG10, ARG11, BRA5 (3)    | FRA2, GER4, JAP6 (3)   | **6** (alto)|
| C       | ARG10 (1)                 | GER4 (1)               | **2** (medio)|

Tal como pide el enunciado: B (con `ARG10, ARG11, BRA5`) obtiene
`match_count` mayor que C (con solo `ARG10`). ✅ El ranking refleja esta
diferencia (B antes que C).

## 6. Intercambio bidireccional (sección 4)

Para B:
- `stickers_i_need_that_user_has = ["ARG10","ARG11","BRA5"]` → lo que A
  necesita y B tiene repetido.
- `stickers_user_needs_that_i_have = ["FRA2","GER4","JAP6"]` → lo que B
  necesita y A tiene repetido.

Ambas direcciones se calculan y muestran correctamente, de forma
independiente (no es necesario que coincidan en cantidad). ✅

## 7. Ordenamiento (sección 5)

Orden esperado: 1º mayor `match_count`, 2º menor `distance_km` (nulo al
final).

| Orden | Usuario | match_count | distance_km |
|-------|---------|--------------|--------------|
| 1     | B       | 6            | 1.4          |
| 2     | C       | 2            | 8.1          |
| 3     | H       | 1            | 5.2          |
| 4     | I       | 1            | 5.8          |
| 5     | D       | 1            | 386.6        |
| 6     | G       | 1            | null         |
| 7     | E       | 0            | 646.8        |

El resultado real de `/api/nearby` coincide exactamente con esta tabla.
Dentro del grupo `match_count=1` (H, I, D, G), el orden por distancia es
correcto (`5.2 < 5.8 < 386.6 < null`), y el caso sin ubicación (`G`) queda
al final del grupo en vez de romper el ordenamiento o ir primero. ✅

## 8. Mensajes de contacto (sección 6)

| Usuario | "A mí me interesan" | "Yo tengo repetidas que quizás te sirven" |
|---------|----------------------|---------------------------------------------|
| B (alto)| ARG10, ARG11, BRA5   | FRA2, GER4, JAP6                             |
| C (medio)| ARG10               | GER4                                         |
| D (bajo, sin email)| MEX3     | (ninguna)                                     |
| H (sin repetidas)| (ninguna)  | FRA2                                          |
| I (sin faltantes)| ARG10     | (ninguna)                                     |
| G (sin ubicación)| ARG10     | (ninguna)                                     |
| E (0 coincidencias)| (ninguna) | (ninguna)                                  |

Todos los mensajes:
- Empiezan con `Hola, soy Fer.` (usa `display_name`, correcto).
- Incluyen el texto fijo "Vi en StickerControl 2026 que estamos cerca...".
- Usan `(ninguna)` como fallback cuando una lista está vacía — formato
  correcto y sin romper el template.
- Terminan con `¿Te interesa coordinar?`.

Ejemplo completo (B):

```
Hola, soy Fer.
Vi en StickerControl 2026 que estamos cerca y tenemos figuritas para intercambiar.

A mi me interesan:
ARG10, ARG11, BRA5

Yo tengo repetidas que quizas te sirven:
FRA2, GER4, JAP6

¿Te interesa coordinar?
```

## 9. Enlaces WhatsApp / Email (sección 7)

Usando el texto de B (`urllib.parse.quote`, equivalente a
`encodeURIComponent` usado en `Nearby.jsx`):

- **WhatsApp**: `https://wa.me/5491122223333?text=Hola%2C%20soy%20Fer.%0AVi%20en%20StickerControl%202026...%C2%BFTe%20interesa%20coordinar%3F`
- **Email**: `mailto:b@example.com?subject=Intercambio%20de%20figuritas%20StickerControl%202026&body=Hola%2C%20soy%20Fer.%0AVi%20en%20StickerControl%202026...%C2%BFTe%20interesa%20coordinar%3F`

Verificado:
- Saltos de línea → `%0A` (correcto para ambos esquemas).
- Espacios → `%20`.
- Comas/dos puntos/signos de pregunta → `%2C` / `%3A` / `%3F`.
- `¿` (U+00BF, fuera de ASCII) → `%C2%BF` (UTF-8 de 2 bytes), se decodifica
  correctamente.
- El número de WhatsApp se concatena tal cual (`5491122223333`, sin `+` ni
  espacios) — coincide con el formato pedido en el formulario de perfil
  ("con código de país, sin + ni espacios").

✅ Encoding correcto en ambos casos.

## 10. Edge cases (sección 8)

| Edge case | Usuario | Resultado |
|-----------|---------|-----------|
| Sin ubicación (`lat`/`lon=null`) | G | `distance_km: null` en `/api/nearby`; no rompe el ordenamiento (va al final de su grupo de `match_count`); `contact-message` funciona normal. |
| Sin `contact_email` | D | `contact_email: null` en `/api/nearby`; en el frontend, el botón "Contactar por email" no se renderiza (`{user.contact_email && ...}`). |
| Sin `contact_whatsapp` | E | `contact_whatsapp: null`; botón WhatsApp no se renderiza. |
| Perfil privado (`is_public=false`) | F | **No aparece** en `/api/nearby` aunque tenga el match más alto (9). |
| Sin repetidas (0 en todo su catálogo) | H | `stickers_i_need_that_user_has: []`, `match_count` se calcula solo con `stickers_user_needs_that_i_have`. No genera error ni `match_count` negativo. |
| Sin faltantes (0 en todo su catálogo) | I | `stickers_user_needs_that_i_have: []`, simétrico al caso anterior. |
| Coordenadas nulas | G | Igual que "sin ubicación" (mismo campo). |
| `contact-message` a usuario **privado** (F) | F | **200 OK**, devuelve el texto completo con sus 5+4 coincidencias — ver bug B1 más abajo. |
| `contact-message` a usuario inexistente | 999 | `404 {"detail":"Usuario no encontrado"}` — correcto. |
| `contact-message` a uno mismo | 1 | `200 OK`, devuelve "(ninguna)" / "(ninguna)" (intersección de mis faltantes con mis propias repetidas es siempre vacía) — no es un error, pero es un mensaje sin sentido si se llega a generar en el frontend. |
| Mi propio `is_public=false` | A | `/api/nearby` sigue devolviendo resultados normalmente — ver nota N1. |

## 11. Mediciones (sección 9)

- **Usuarios simulados**: 9 (1 "yo" + 8 otros, de los cuales 7 públicos y 1
  privado).
- **Coincidencias detectadas**: 6 usuarios con `match_count > 0` (B=6, C=2,
  H=1, I=1, D=1, G=1) + 1 con `match_count = 0` (E) + 1 oculto por privacidad
  (F, hubiera sido 9).
- **Tiempo de respuesta `GET /api/nearby`** (9 usuarios, 11 stickers, 5
  requests consecutivos): `0.019s`, `0.019s`, `0.023s`, `0.025s`, `0.049s`
  → ~20-50 ms. La implementación actual recalcula
  `get_missing_and_duplicate_codes()` para **cada** usuario público en cada
  request (consulta completa de `master_stickers` + `user_stickers` por
  usuario) — con 9 usuarios y 11 stickers no es un problema, pero ver riesgo
  R1 sobre escalabilidad.
- **Tiempo de respuesta `GET /api/nearby/{id}/contact-message`**: ~8-12 ms.
- **Ranking generado**: ver tabla de la sección 7 (orden correcto en los 7
  usuarios públicos).

## 12. Bugs encontrados

- **B1 — `contact-message` no respeta `is_public`** (privacidad,
  severidad media): `GET /api/nearby/{user_id}/contact-message` no filtra
  por `is_public`. Si alguien conoce (o adivina, dado que los IDs son
  secuenciales: 1, 2, 3...) el `user_id` de un perfil **privado**, puede
  obtener el texto de coincidencias de ese usuario (qué le falta, qué tiene
  repetido) aunque ese usuario haya elegido no aparecer en "Usuarios cerca".
  No expone `contact_email`/`contact_whatsapp` (ese endpoint no los
  devuelve), pero sí expone qué figuritas le faltan/sobran — información que
  el usuario privado no consintió compartir.
  - *Nota*: en la práctica el riesgo es bajo porque el frontend solo ofrece
    el botón "Copiar mensaje" para los `user_id` que vienen de
    `/api/nearby` (que ya excluye privados), pero el endpoint en sí no tiene
    esa protección si se llama directamente (p.ej. con la consola del
    navegador o `curl`).

No se encontraron bugs en el cálculo de `match_count`, `distance_km`,
ordenamiento, ni en el formato de los mensajes/enlaces — todos los casos
probados dieron el resultado esperado.

## 13. Riesgos encontrados

- **R1 — Costo O(usuarios públicos × tamaño del catálogo) en cada
  `/api/nearby`**: por cada usuario público se recorre `master_stickers`
  completo (980 filas en la base real) más sus `user_stickers`. Con 9
  usuarios de prueba y 11 stickers, la respuesta tardó ~20-50 ms. Con el
  catálogo real (980 stickers) y, digamos, decenas/cientos de usuarios
  públicos simultáneos durante el Mundial, el tiempo crecería linealmente
  con ambos factores. Para el uso esperado (app de corta duración, pocos
  usuarios concurrentes por ciudad) probablemente sigue siendo aceptable,
  pero es el punto más sensible si la adopción es mayor a la esperada.
- **R2 — IDs de usuario secuenciales y endpoint de contact-message sin
  control de privacidad** (relacionado con B1): permite enumerar
  `/api/nearby/{1..N}/contact-message` y obtener información de matching de
  cualquier usuario, público o no, sin necesidad de que aparezca en el
  listado.
- **R3 — Sin paginación ni límite en `/api/nearby`**: la respuesta incluye
  *todos* los usuarios públicos (excepto uno mismo), sin límite de
  distancia ni cantidad. Si en algún momento hay muchos usuarios públicos en
  ciudades muy distintas, el listado podría volverse largo y poco útil (un
  usuario en Ushuaia vería resultados de alguien a 3000 km con
  `match_count` alto antes que alguien cercano con `match_count` bajo,
  porque el orden prioriza `match_count` sobre distancia). Es una decisión
  de diseño consciente (documentada en `NEARBY_USERS_MVP.md`), pero conviene
  tenerlo presente: para un Mundial con afluencia global, el "match alto
  pero a 3000 km" puede no ser tan útil en la práctica como un "match medio
  a 500 metros".
- **R4 — Mensaje de contacto a uno mismo no tiene guardas**: no es
  explotable ni dañino, pero si en el futuro se agrega un botón "ver mi
  propio mensaje" (p.ej. para previsualizar), el resultado actual
  ("A mí me interesan: (ninguna) / Yo tengo repetidas que quizás te sirven:
  (ninguna)") no tiene sentido y debería filtrarse en el frontend.
- **N1 (nota, no es un riesgo de seguridad)**: mi propio `is_public` no
  afecta lo que yo veo en `/api/nearby` — puedo "mirar" a otros
  coleccionistas sin exponerme yo. Esto es coherente con el modelo de
  privacidad opt-in (cada usuario decide si lo ven, no si él puede ver), pero
  vale la pena que el equipo confirme que es el comportamiento deseado (vs.
  exigir reciprocidad: "solo ves a otros si vos también sos visible").

## 14. Mejoras sugeridas (no implementadas — solo sugerencias)

1. Filtrar por `is_public` también en `get_contact_message` (corrige B1/R2),
   o al menos no incluir el detalle de coincidencias si el usuario consultado
   es privado.
2. Considerar un límite de distancia configurable (p.ej. "solo mostrar
   usuarios a menos de X km") para mitigar R3, especialmente útil si la app
   tiene adopción internacional durante el Mundial.
3. Cachear `get_missing_and_duplicate_codes()` por usuario dentro de un
   mismo request de `/api/nearby` si en el futuro se llama más de una vez
   (hoy se llama una vez por usuario, no es un problema actual, pero si R1
   se vuelve relevante esto ayudaría).
4. En el frontend, evitar ofrecer "Copiar mensaje"/contacto para el propio
   `user_id` si alguna vista futura llega a listar al usuario actual (hoy no
   ocurre, pero ver R4).

## 15. Conclusión

**¿Es "Usuarios cerca" suficientemente útil para un coleccionista real
durante el Mundial 2026?**

**Sí, para el alcance de un MVP de pocos días/semanas.** La lógica central
— cálculo de coincidencias bidireccionales, distancia aproximada,
ordenamiento por relevancia y generación de mensaje listo para WhatsApp/email
— funciona correctamente en los 9 casos probados (alta/media/baja/nula
coincidencia, <2 km/<10 km/>100 km/sin ubicación, y los 7 edge cases
pedidos). El flujo "encontrar a alguien cerca con quien me convenga
intercambiar → copiar mensaje → contactar por WhatsApp" está completo y sin
errores de cálculo.

La única falla real de privacidad (B1/R2) es de severidad media y de
explotación poco probable en el uso normal (requiere conocer/adivinar un
`user_id` privado y llamar al endpoint directamente). El riesgo de
escalabilidad (R1) y el de relevancia geográfica con adopción masiva (R3) no
son bloqueantes para el uso esperado (volumen bajo/medio, ventana de pocas
semanas), pero conviene que el equipo los tenga presentes si la función se
promociona ampliamente.
