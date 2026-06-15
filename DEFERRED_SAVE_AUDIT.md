# Auditoría: guardado diferido en StickerCard (Pegar / +1 / -1 / Marcar faltante)

**Solo auditoría — sin implementación.** Objetivo: evaluar qué tan complejo
es que las 4 acciones de colección (`Pegar`/`Despegar`, `+1`, `-1`, `Marcar
faltante`) dejen de llamar al backend al instante y queden en un borrador
local, enviándose solo al presionar un botón **Guardar** (que hoy ya existe,
pero solo para `notes`).

## 1. Cómo funciona hoy (arquitectura actual)

- `StickerCard.jsx` es el único punto de UI con las 4 acciones + notas.
  Recibe `sticker` (objeto `StickerOut` completo: `quantity`, `is_pasted`,
  `notes`, `status`, `repetidas`, ya calculados por el backend) y dos
  callbacks: `onAction(id, action)` y `onSaveNotes(id, notes)`.
- Cada botón de acción llama `onAction` **inmediatamente** → el padre
  (`Search.jsx` o `Album.jsx`) invoca `STICKER_ACTIONS[action](id)` →
  `POST /api/collection/{id}/{paste|unpaste|increment|decrement|mark-missing}`
  → el backend muta `UserSticker` y devuelve el `StickerOut` ya recalculado
  (`status`/`repetidas` vía `status.py` + `crud.to_sticker_out`) → el padre
  reemplaza ese sticker en su estado (`items` en Search, `selectedSticker`
  en Album).
- **Notas ya son "diferidas"**: hay un `useState(notes)` local en
  `StickerCard` + botón "Guardar" que llama `onSaveNotes` → `PATCH
  /api/collection/{id}/notes`. Es el único precedente de "editar local,
  guardar aparte" que existe hoy.
- `StickerDetailModal.jsx` es un wrapper delgado: monta el mismo
  `StickerCard` con los mismos callbacks, usado por `Album.jsx` para el
  detalle de una figurita.
- Backend: los 5 endpoints de `/api/collection/*` son **acciones relativas**
  (incrementar/decrementar/toggle), no "set absoluto". No existe un endpoint
  que reciba `{quantity, is_pasted, notes}` y los aplique de una sola vez.

## 2. Qué implica "no persistir hasta Guardar"

Cambia el modelo de "fuente de verdad": hoy la UI siempre refleja el estado
canónico del backend (cada click = respuesta autoritativa inmediata). Con
guardado diferido, `StickerCard` necesita su **propio estado borrador**
(`draftQuantity`, `draftIsPasted`, `draftNotes`) distinto del `sticker` que
llega por props, más:

- Recalcular `status` y `repetidas` **en el frontend** a partir del borrador,
  duplicando las reglas de `backend/app/status.py`
  (`compute_status`/`compute_repetidas` — 6 líneas de lógica simple, pero
  es lógica de negocio duplicada en dos lenguajes/repos que debe mantenerse
  sincronizada).
- Detectar "hay cambios sin guardar" (dirty) comparando borrador vs. `sticker`
  original, para habilitar/deshabilitar "Guardar" y mostrar algún indicador.
- Resetear el borrador cuando `sticker` cambia "desde afuera" (después de
  guardar, o al abrir el modal con otra figurita) — hoy `StickerCard` no
  tiene `useEffect` para esto porque no lo necesita.
- Decidir **cómo se envía el borrador al backend**, dado que los endpoints
  actuales son relativos:
  - **Opción A (recomendada): nuevo endpoint backend** `PATCH
    /api/collection/{id}` que reciba `{quantity, is_pasted, notes}` (set
    absoluto) y devuelva el `StickerOut` recalculado — un solo request
    atómico al "Guardar". Requiere tocar `collection.py`, `schemas.py`
    (nuevo `CollectionUpdate`), y opcionalmente reusar/eliminar los 5
    endpoints relativos (o dejarlos para compatibilidad).
  - **Opción B (sin tocar backend): "replay" de deltas** — al guardar,
    calcular cuántas veces cambió `is_pasted` (0 o 1 llamadas
    `paste`/`unpaste`), la diferencia de `quantity` (N llamadas
    `increment`/`decrement`), y la nota (`PATCH notes` si cambió). Esto son
    hasta **1 + N + 1 requests secuenciales** por "Guardar", no atómico: si
    falla a mitad de camino, el estado del backend queda inconsistente con
    el borrador y con lo que el usuario ve. Frágil y más lento, pero no
    requiere cambios de backend.

  La auditoría recomienda **Opción A** por simplicidad y atomicidad, pero
  implica un cambio de backend (fuera del alcance de "no implementar
  todavía", solo se documenta como prerequisito).

## 3. Archivos afectados (si se implementara)

| Archivo | Tipo de cambio | Detalle |
|---|---|---|
| `frontend/src/components/StickerCard.jsx` | **Alto** | Estado borrador (`quantity`, `is_pasted`, `notes`), recálculo local de `status`/`repetidas`, dirty-tracking, unificar el botón "Guardar" para las 4 acciones + notas, reset de borrador cuando cambia `sticker.id`. |
| `frontend/src/api/stickerActions.js` | **Medio** | Reemplazar o complementar el mapa de acciones inmediatas por una función `saveSticker(id, {quantity, is_pasted, notes})` (Opción A) o por un orquestador de replay (Opción B). |
| `frontend/src/pages/Search.jsx` | **Medio** | `handleAction`/`handleSaveNotes` ya no se llaman por click de botón; se reemplazan por un único `handleSave(id, draft)` que llama al nuevo endpoint y actualiza `items`. Sin cambios en el fetch/debounce de búsqueda. |
| `frontend/src/pages/Album.jsx` | **Medio** | Igual que Search para `selectedSticker`. Además: `loadAlbum()` (que refresca la grilla/colores/resumen) debe pasar a ejecutarse **solo después de Guardar**, no en cada click. Decidir comportamiento al cerrar el modal con cambios sin guardar (descartar silenciosamente vs. confirmar). |
| `frontend/src/components/StickerDetailModal.jsx` | **Bajo** | Si `StickerCard` mantiene estado interno por figurita, el modal necesita forzar reset al cambiar de sticker (ej. `key={sticker?.id}` para remount, o un `useEffect` en `StickerCard`). |
| `backend/app/routes/collection.py` + `schemas.py` + `crud.py` | **Medio** (solo si Opción A) | Nuevo endpoint `PATCH /collection/{id}` con `CollectionUpdate {quantity, is_pasted, notes}`, validación (`quantity >= 0`), devuelve `StickerOut` vía `to_sticker_out`. Los 5 endpoints relativos pueden quedar (no rompen nada) o deprecarse después. |
| `frontend/src/utils/*`, `StatusBadge.jsx` | **Bajo** | Sin cambios estructurales, pero `StatusBadge` ahora recibe un `status` calculado en frontend (borrador) en vez de siempre del backend — debe seguir funcionando igual porque son los mismos 4 strings. |

## 4. Impacto en el modal de Álbum (`StickerDetailModal` + `Album.jsx`)

- **Hoy**: cada click en el modal dispara `onAction` → backend → `loadAlbum()`
  (refresca toda la grilla: colores de tiles, % y contadores de `summary`).
  El modal y la grilla quedan siempre sincronizados.
- **Con guardado diferido**: mientras el modal está abierto con cambios sin
  guardar, la grilla detrás **no debe cambiar** (consistente con "no
  persistir"), pero esto puede leerse como un bug ("toqué Pegar y no pasó
  nada en el álbum"). Hay que decidir:
  - (a) Aceptarlo tal cual: la grilla solo se actualiza tras "Guardar"
    (`loadAlbum()` se mueve de cada acción → solo al guardar). Más simple,
    pero el usuario no tiene feedback visual fuera del modal hasta guardar.
  - (b) Mostrar un indicador "cambios sin guardar" dentro del modal (más
    simple) en vez de tocar la grilla — recomendado.
- **Cierre del modal con cambios sin guardar**: hoy `onClose` simplemente
  hace `setSelectedSticker(null)`, sin pérdida de datos porque no hay
  borrador. Con borrador, cerrar = descartar cambios silenciosamente, salvo
  que se agregue una confirmación ("¿Descartar cambios?"). No especificado
  por el usuario — **decisión pendiente**.
- El modal en sí (`StickerDetailModal.jsx`) requiere un cambio mínimo (reset
  de borrador al cambiar de sticker), el grueso del impacto es en
  `Album.jsx` (cuándo se llama `loadAlbum()` y qué pasa al cerrar).

## 5. Impacto en Buscar (`Search.jsx`)

- Cada resultado de búsqueda es un `StickerCard` independiente; con borrador
  local, **cada card mantiene su propio estado sin guardar** — esto ya es
  natural porque cada `StickerCard` es una instancia de componente separada,
  no requiere cambios adicionales de aislamiento.
- **Re-búsqueda con cambios sin guardar**: el `useEffect` de `Search.jsx`
  reemplaza `items` completo cada vez que cambia `query` (debounce 300ms,
  min 2 caracteres). Si el usuario edita una card (sin guardar) y luego
  busca otra cosa, esa card desaparece de `items` y **el borrador se pierde
  silenciosamente** (se desmonta el componente). Esto es coherente con
  "estado local temporal", pero conviene documentarlo como comportamiento
  esperado (o, en una iteración futura, avisar "tenés cambios sin guardar"
  antes de cambiar de búsqueda — no solicitado ahora).
- No afecta el límite de 10 resultados, el debounce, ni el mensaje guía.

## 6. Impacto en Faltantes / Repetidas (`Missing.jsx`, `Duplicates.jsx`)

- Estas dos páginas **no usan `StickerCard` ni `STICKER_ACTIONS`** (confirmado
  por búsqueda en el código) — consumen directamente `/api/reports/missing`
  y `/api/reports/duplicates`, que leen `user_stickers` desde la base.
- **Impacto de código: ninguno.**
- **Impacto de comportamiento**: si el usuario marca una figurita como
  "Pegada" en Buscar/Álbum pero no presiona "Guardar", esa figurita **sigue
  apareciendo como faltante/repetida** en estas pantallas (porque el backend
  todavía no se actualizó) — es exactamente el efecto esperado por el
  pedido, pero es una fuente probable de confusión ("la marqué pegada y
  sigue en Faltantes"). Vale la pena un mensaje/tooltip tipo "los cambios se
  reflejan en Faltantes/Repetidas después de Guardar".

## 7. Impacto en hooks existentes

- **No existen hooks personalizados hoy** (`useSticker`, `useCollection`,
  etc.) — toda la lógica está inline con `useState`/`useEffect` en
  `StickerCard.jsx`, `Search.jsx` y `Album.jsx`. Por lo tanto, **no hay hooks
  existentes que se rompan**.
- La forma más limpia de implementar esto sería extraer un hook nuevo, ej.
  `useStickerDraft(sticker, onSave)` (estado borrador + dirty + recálculo de
  status/repetidas + función `save()`), usado dentro de `StickerCard`. Esto
  es una **adición**, no una modificación de algo existente, y evita
  duplicar la lógica de borrador si en el futuro se necesita en otro lugar.
  No es estrictamente necesario (podría ir todo inline en `StickerCard`),
  pero reduce el tamaño/complejidad del componente.

## 8. Riesgos

- **Duplicación de lógica de negocio**: `compute_status`/`compute_repetidas`
  (hoy solo en `backend/app/status.py`) deben replicarse en JS para que el
  borrador muestre `StatusBadge`/cantidad/repetidas correctos antes de
  guardar. Riesgo de que las reglas diverjan si se cambian en un solo lado
  a futuro (mitigable con un comentario cruzado o, si se quiere, generar el
  JS desde la regla Python — fuera de alcance).
- **Atomicidad del guardado**: sin un endpoint nuevo (Opción A), "Guardar"
  implica varias llamadas HTTP secuenciales no atómicas (Opción B) — riesgo
  de estado parcial si una falla (ej. notes se guarda pero el toggle
  "Pegar" falla). Con Opción A el riesgo desaparece pero requiere tocar
  backend.
- **Pérdida silenciosa de borradores**: al re-buscar (Search) o cambiar de
  figurita en el modal (Álbum) sin guardar, el borrador se pierde sin aviso.
  Es lo pedido ("estado local temporal"), pero es una decisión de UX que
  conviene confirmar explícitamente con el usuario final del producto.
- **Inconsistencia visual temporal**: Álbum (grilla/resumen) y
  Faltantes/Repetidas no reflejan cambios sin guardar — puede percibirse
  como bug si no se comunica con un indicador claro de "sin guardar".
- **Regresión de UX en notas**: hoy "Guardar" solo aplica a `notes`; si se
  unifica en un solo botón "Guardar" para las 4 acciones + notas, hay que
  asegurarse de que sigue siendo obvio que notas también se guardan ahí (no
  es un cambio de riesgo alto, pero es un cambio de comportamiento percibido
  por el usuario final).

## 9. Estimación de complejidad

**Media** (no trivial, pero acotada). Desglose aproximado:

| Tarea | Complejidad |
|---|---|
| `StickerCard.jsx`: estado borrador, dirty-tracking, recálculo local de status/repetidas, botón Guardar unificado, reset al cambiar `sticker` | Media-Alta |
| Nuevo endpoint backend `PATCH /collection/{id}` (Opción A recomendada) + schema + crud | Media |
| `Search.jsx`: reemplazar `handleAction`/`handleSaveNotes` por `handleSave` | Baja-Media |
| `Album.jsx`: mover `loadAlbum()` a post-guardado, decidir UX de cierre de modal con cambios sin guardar | Media |
| `StickerDetailModal.jsx`: reset de borrador al cambiar de sticker (`key` o `useEffect`) | Baja |
| Pruebas manuales: Buscar (varias cards con borradores independientes), Álbum (modal + grilla + resumen), Faltantes/Repetidas (verificar que no cambian hasta Guardar), `npm run build` | Media |

**Decisiones de producto pendientes antes de implementar**:
1. ¿Endpoint nuevo en backend (Opción A) o replay de llamadas existentes
   (Opción B)? — se recomienda A.
2. ¿Qué pasa si se cierra el modal del Álbum o se cambia la búsqueda con
   cambios sin guardar? (descartar silenciosamente vs. confirmar).
3. ¿Se necesita un indicador visual de "cambios sin guardar" en la card?
   (recomendado, bajo costo).
4. ¿El botón "Guardar" reemplaza/unifica el botón actual de notas, o
   convive como uno solo para todo el card? (se asume unificado).

**Estimación total**: aproximadamente **medio día a un día** de trabajo
enfocado (incluye el endpoint backend de Opción A), una vez resueltas las
4 decisiones de producto arriba.
