# Mobile Implementation Backlog V2 — StickerControl 2026

Revisión del backlog (`MOBILE_IMPLEMENTATION_BACKLOG.md`) tras refocus de
prioridades. Solo planificación — sin código, sin análisis de CSS.

## 0. Cambio de enfoque

### Hallazgo retirado

En V1, **A1** ("las figuritas 11-19 no son visibles en algunas tarjetas del
Álbum") se basaba en una lectura literal de la captura `1000666237.jpg`,
interpretada como un posible problema de overflow/grid.

**Se retira esa hipótesis.** La captura fue tomada con el navegador
móvil en zoom manual del usuario, por lo que la ausencia visual de 11-19
en esa captura puntual no es evidencia de contenido inaccesible ni de un
bug de layout. No hay evidencia de overflow oculto ni de pérdida de
contenido.

### Pregunta que reemplaza a A1

La pregunta que guía este backlog ya no es *"¿qué hace que las figuritas
11-19 desaparezcan?"* sino:

> **¿Qué hace que un coleccionista necesite hacer zoom para usar la
> aplicación cómodamente?**

El propio acto de hacer zoom **es** el hallazgo: es evidencia de
comportamiento real de un usuario que indica que, a la escala por defecto,
los elementos son demasiado pequeños para leerse y/o tocarse con
comodidad. Esto reorienta el foco de "¿se pierde contenido?" (no hay
evidencia de eso) a "¿el contenido visible es usable a su tamaño actual?"
(sí hay evidencia de que no, dado que el usuario necesitó zoom).

### Qué pasa con el resto de A1/A2 de V1

- Las capturas 1 y 4 siguen siendo evidencia válida de **tamaño de badges,
  tipografía y densidad** (eso no depende del zoom — son las clases/medidas
  reales del componente). Esa evidencia se reutiliza en los nuevos ítems
  P1 de este documento.
- **A2** (acordeón para colapsar tarjetas de país) de V1 ya no se justifica
  por "contenido inaccesible" (esa justificación dependía de A1, retirado).
  Sigue siendo relevante por **scroll excesivo** (49 tarjetas expandidas),
  pero se reclasifica como mejora secundaria — ver §5.

---

## 1. Nueva Prioridad P1 — Ergonomía táctil, legibilidad y densidad

Tema común: **Álbum, Faltantes y Repetidas** comparten el mismo patrón de
"badge numerado pequeño en grilla densa". El zoom reportado por el usuario
es la señal de que este patrón, tal como está, no es cómodo de usar sin
ayuda del navegador.

### P1-1. Tamaño táctil de badges — Álbum

- **Problema real**: los badges numerados de cada tarjeta de país (1-20,
  más "00" en Especiales) tienen una altura de referencia de ~32px
  (`h-8`), por debajo del mínimo de área táctil recomendado (~44-48px en
  Material Design / Android / WCAG). Con 8-10 badges por fila, el ancho
  individual también queda reducido.
- **Evidencia**:
  - Capturas `1000666185.jpg` y `1000666237.jpg`: badges visiblemente
    pequeños, números de 1-2 cifras en tipografía reducida, muy juntos
    entre sí.
  - Comportamiento reportado del usuario: necesidad de hacer zoom para
    interactuar — comportamiento típico cuando los objetivos táctiles
    están por debajo del umbral cómodo (~7-9mm reales en pantalla).
- **Componente / archivo** (referencia, sin tocar código ahora):
  `CountryCard` en `frontend/src/pages/Album.jsx`.
- **Impacto UX**: **Alto** — afecta la pantalla con más interacciones
  táctiles repetidas de toda la app (49 tarjetas x hasta 20 badges).
- **Complejidad**: **Media** — agrandar el badge implica recalcular cuántas
  columnas entran por fila en el ancho real de mobile (ver P1-4, están
  relacionadas).
- **Riesgo desktop**: **Medio** — más alto por tarjeta × 49 tarjetas =
  más alto total de página; verificar que la columna `md:max-w-2xl`
  (672px) siga viéndose equilibrada con badges más grandes.
- **Prioridad**: **P1**

### P1-2. Tamaño táctil de badges — Faltantes

- **Problema real**: los badges de `Missing.jsx` (`<span>` con
  `rounded-full px-2 py-1 text-xs`) son aún más compactos que los del
  Álbum — no tienen una altura mínima explícita, dependen solo del
  padding alrededor de texto `text-xs` (~12px).
- **Evidencia**: revisión de código previa (fix del código "00") confirmó
  esta clase exacta en `Missing.jsx` línea ~54. No hay captura dedicada de
  esta pantalla, pero el componente es estructuralmente más pequeño que el
  ya observado en Álbum (que sí tiene evidencia visual de necesitar zoom).
  Si el patrón "más comprimido que Álbum" se confirma visualmente, el
  problema sería igual o mayor que P1-1.
- **Componente / archivo**: badges `<span>` en
  `frontend/src/pages/Missing.jsx`.
- **Impacto UX**: **Alto** (mismo razonamiento que P1-1, agravado por ser
  un componente aún más pequeño).
- **Complejidad**: **Baja** — `flex-wrap` se reacomoda solo; es un cambio
  de padding/tamaño de fuente en un único `<span>`, sin recalcular columnas
  de un `grid`.
- **Riesgo desktop**: **Bajo** — `flex-wrap` no tiene las restricciones de
  columnas fijas que sí tiene el `grid` del Álbum.
- **Prioridad**: **P1**

### P1-3. Tamaño táctil de badges — Repetidas

- **Problema real**: idéntico a P1-2, en `Duplicates.jsx` (`<span>` con
  `rounded-full px-2 py-1 text-xs`, además del sufijo `(xN)` que puede
  hacer el texto más largo y comprimido).
- **Evidencia**: misma base que P1-2 — mismo patrón de componente,
  confirmado por revisión de código en el fix anterior. Sin captura
  dedicada.
- **Componente / archivo**: badges `<span>` en
  `frontend/src/pages/Duplicates.jsx`.
- **Impacto UX**: **Alto** (mismo razonamiento; el sufijo `(xN)` agrava la
  legibilidad cuando el badge ya es pequeño).
- **Complejidad**: **Baja**
- **Riesgo desktop**: **Bajo**
- **Prioridad**: **P1**

> **Nota de secuencia**: P1-2 y P1-3 son cambios casi idénticos en archivos
> hermanos (`Missing.jsx` / `Duplicates.jsx`) — conviene ejecutarlos juntos
> en la misma sesión, aunque se documenten como tareas separadas para
> trazabilidad.

### P1-4. Legibilidad de números, badges e indicadores de estado

- **Problema real**: además del tamaño del contenedor (P1-1 a P1-3), el
  **texto** dentro de esos elementos —y en otros indicadores de estado— usa
  tamaños de fuente muy chicos: `text-xs` (~12px) en badges y en las líneas
  de resumen ("X faltantes · Y repetidas"), `text-[10px]` en banderas y en
  las etiquetas de la navegación inferior, y los anillos de progreso
  (`ProgressRing`) muestran un porcentaje en texto pequeño dentro de un
  círculo de ~50-56px (Álbum) o ~168px (Dashboard, este último más legible).
  La combinación tamaño-de-contenedor + tamaño-de-fuente es lo que más
  probablemente dispara el zoom manual del usuario, más que cualquier
  elemento aislado.
- **Evidencia**:
  - Captura `1000666185.jpg`: texto "X/20 pegadas" y "Y faltantes · Z
    repetidas" en cada tarjeta de país, a tamaño visualmente muy pequeño
    junto al anillo de ~50px.
  - Captura `1000666235.jpg`: etiquetas de banderas (`MEX`, `RSA`, etc.) en
    `text-[10px]`.
  - Capturas `1000666185.jpg` y `1000666236.jpg`: etiquetas de la
    navegación inferior en `text-[10px]`.
- **Componente / archivo**: transversal —
  `frontend/src/pages/Album.jsx` (texto de `CountryCard`),
  `frontend/src/pages/Dashboard.jsx` (etiquetas de banderas),
  `frontend/src/components/Layout.jsx` (etiquetas de nav — solo el
  *tamaño de fuente*, no la cantidad de ítems, ver §3).
- **Impacto UX**: **Alto** — es la causa más transversal del "todo se ve
  chiquito" y, por lo tanto, del zoom.
- **Complejidad**: **Media** — no es un cambio de una sola clase, sino una
  revisión de la escala tipográfica usada en varios componentes a la vez
  (consistencia entre pantallas).
- **Riesgo desktop**: **Bajo-Medio** — agrandar texto en componentes
  pequeños (badges, anillos) tiene bajo riesgo; agrandar etiquetas de la
  nav inferior podría requerir más ancho por ítem (relacionado con §3, pero
  sin asumir que hay que reducir la cantidad de ítems).
- **Prioridad**: **P1**

### P1-5. Uso del ancho disponible en mobile (Álbum)

- **Problema real**: el fix de layout previo ya logró que el contenedor
  principal ocupe el 100% del ancho en mobile, pero la grilla interna de
  badges del Álbum sigue usando una cantidad fija de columnas (8 por
  defecto, 10 desde `sm:`) pensada para encajar muchos elementos chicos en
  poco espacio — es decir, el ancho ganado por el fix anterior no se está
  traduciendo en badges más grandes, sino en más columnas del mismo tamaño
  pequeño. Esta tarea es la contracara directa de P1-1: para agrandar los
  badges (P1-1) hay que decidir cuántas columnas son razonables para el
  ancho real de un teléfono, y esa decisión es justamente "mejorar el uso
  del ancho disponible".
- **Evidencia**: capturas `1000666185.jpg` y `1000666237.jpg` — 8-10
  badges por fila ocupando todo el ancho de pantalla, cada uno muy
  pequeño; el ancho total disponible ya es completo (gracias al fix
  previo), pero está repartido en demasiadas columnas chicas.
- **Componente / archivo**: `CountryCard` en `frontend/src/pages/Album.jsx`
  (clase `grid grid-cols-8 sm:grid-cols-10`).
- **Impacto UX**: **Alto** (es, en la práctica, la misma decisión de diseño
  que P1-1 — se documenta aparte porque el ítem 3 de la nueva P1 lo pide
  explícitamente, pero **se recomienda ejecutar P1-1 y P1-5 juntas**).
- **Complejidad**: **Baja-Media** (ver P1-1).
- **Riesgo desktop**: **Medio** (ver P1-1).
- **Prioridad**: **P1** (fusionable con P1-1 en ejecución).

### P1-6. Spacing y densidad visual

- **Problema real**: independientemente del tamaño de cada badge, el
  espacio **entre** elementos es mínimo (`gap-1` ≈ 4px entre badges,
  tarjetas de país con padding moderado y poco aire entre el bloque de
  texto y la grilla de badges). Esta densidad alta contribuye a la
  percepción de "todo apretado" y dificulta distinguir un badge de su
  vecino al tocar, incluso si el tamaño individual del badge aumentara.
- **Evidencia**: capturas `1000666185.jpg` y `1000666237.jpg` — badges
  prácticamente contiguos, sin separación perceptible entre filas/columnas.
- **Componente / archivo**: `CountryCard` en `frontend/src/pages/Album.jsx`
  (clase `gap-1` de la grilla de badges); aplicable también a
  `Missing.jsx`/`Duplicates.jsx` (`flex-wrap gap-1`, a confirmar con
  captura).
- **Impacto UX**: **Medio** — refuerza P1-1/P1-2/P1-3 pero no es, por sí
  sola, la causa principal del zoom.
- **Complejidad**: **Baja** — ajuste de valores de `gap`.
- **Riesgo desktop**: **Bajo** — más espacio entre elementos rara vez rompe
  un layout, en el peor caso aumenta el alto total.
- **Prioridad**: **P1** (de menor esfuerzo dentro del grupo — buen punto de
  partida/quick win antes o junto con P1-1).

---

## 2. Nueva Prioridad P2 — Dashboard

### P2-1. Eliminar espacios muertos y mejorar jerarquía visual

- **Problema real**: el Dashboard deja un espacio vacío de
  aproximadamente la mitad del viewport por debajo de "Accesos rápidos",
  sin contenido ni función. Además, el bloque "hero" (tarjeta verde con
  anillo de progreso) tiene relleno vacío alrededor del anillo, y la
  grilla 2x3 de "Accesos rápidos" deja una celda sin usar (5 elementos en
  grilla par).
- **Evidencia**: captura `1000666236.jpg` — debajo de "Usuarios cerca", el
  resto de la pantalla (más de la mitad del alto visible) está vacío hasta
  la barra de navegación inferior. Captura `1000666235.jpg` — la celda
  vacía de la grilla 2x3 y el espacio alrededor del anillo de progreso
  dentro de la tarjeta verde.
- **Componente / archivo**: estructura general de
  `frontend/src/pages/Dashboard.jsx` (hero card, grilla "Accesos
  rápidos").
- **Impacto UX**: **Alto** — es la primera pantalla que ve el usuario; el
  vacío refuerza directamente la sensación de "página de escritorio
  reducida" descrita en el masterplan original.
- **Complejidad**: **Media** — reordenar/redimensionar secciones
  existentes sin necesitar nuevos datos (los totales ya están disponibles
  en `summary`).
- **Riesgo desktop**: **Bajo** — el Dashboard en desktop tiene más ancho
  relativo de columna; reordenar contenido existente no debería degradarlo,
  en el peor caso agrega scroll leve.
- **Prioridad**: **P2**

### P2-2. CTA principal para el coleccionista

- **Problema real**: ningún elemento del Dashboard comunica "esto es lo
  que deberías hacer ahora". El dato más relevante para un coleccionista
  activo (cantidad de faltantes, ej. "979 faltantes") tiene el mismo peso
  visual que cualquier otro número (repetidas=0, accesos secundarios como
  "Usuarios cerca"). No hay una acción primaria destacada.
- **Evidencia**: capturas `1000666235.jpg` y `1000666236.jpg` — las 3
  tarjetas de estadísticas (Pegadas/Faltantes/Repetidas) tienen idéntico
  tamaño y jerarquía tipográfica; los 5 accesos rápidos también tienen
  idéntico peso visual entre sí, sin distinción de cuál es la acción más
  probable/relevante para el usuario en ese momento.
- **Componente / archivo**: nuevo bloque dentro de
  `frontend/src/pages/Dashboard.jsx` (puede reutilizar el espacio liberado
  por P2-1).
- **Impacto UX**: **Alto** — da una razón de ser al espacio recuperado en
  P2-1 y convierte al Dashboard de "tablero de estado" a "punto de partida
  de la sesión".
- **Complejidad**: **Media** — requiere diseñar un componente nuevo (CTA
  card), aunque con datos ya existentes (`summary.faltantes`,
  enlace a `/faltantes`).
- **Riesgo desktop**: **Bajo** — es contenido adicional; en desktop solo
  añade una sección más a una columna que ya tiene espacio de sobra.
- **Prioridad**: **P2**

> **Nota**: P2-1 y P2-2 están fuertemente acopladas (la CTA de P2-2 es, en
> la práctica, el contenido que llena el vacío de P2-1) — se recomienda
> diseñarlas e implementarlas en la misma sesión.

---

## 3. Nueva Prioridad P3 — Bottom Navigation (evaluación, no rediseño)

### P3-1. Evaluar ergonomía de la navegación inferior (sin asumir rediseño)

- **Problema real**: **a determinar**. La navegación inferior tiene 7
  destinos (Inicio, Buscar, Álbum, Faltantes, Repetidas, Cambios, Cerca),
  cada ícono+etiqueta con ancho ~14% de la pantalla. **No se asume que 7
  ítems sea, por sí mismo, un problema** — la guía de Material Design
  (3-5 destinos) es una recomendación de diseño general, no evidencia de
  que *esta* navegación específica falle para *este* usuario.
- **Evidencia disponible hoy**:
  - Capturas `1000666185.jpg` y `1000666236.jpg` muestran la barra
    completa: 7 íconos (~20px estimado) con etiquetas en `text-[10px]`,
    espaciado mínimo entre ítems.
  - **No hay evidencia** de toques erróneos, quejas sobre navegación, o
    confusión reportada por el usuario respecto a la barra inferior. El
    único comportamiento reportado (zoom) ocurrió en el contenido del
    Álbum, no se asoció a la navegación.
- **Lo que falta para decidir**: antes de proponer cualquier cambio
  estructural (ej. reducir a 5 ítems + menú "Más"), se necesita evidencia
  específica de la navegación, por ejemplo:
  1. Medición real en el dispositivo: tamaño en px/dp de cada ícono,
     etiqueta y área táctil total por ítem, comparado contra el mínimo de
     48dp.
  2. Observación de uso: ¿el usuario toca el destino que intenta, a la
     primera, consistentemente? ¿Hay reportes de "tocar Repetidas y caer en
     Cambios" o similar?
  3. Una captura dedicada de la barra (zoom normal, sin zoom manual) que
     permita medir proporciones reales.
- **Componente / archivo** (solo referencia para cuando haya evidencia):
  `frontend/src/components/Layout.jsx` (`NAV_ITEMS`, render del `<nav>`).
- **Impacto UX**: **Por determinar** — potencialmente Medio si la medición
  confirma íconos/áreas táctiles por debajo del mínimo; podría ser Bajo si
  los tamaños están dentro de un rango aceptable y el usuario no reporta
  fricción real.
- **Complejidad**:
  - Recolectar evidencia (medición + observación): **Baja**.
  - Cualquier acción correctiva *si* la evidencia la justifica: Baja
    (aumentar tamaño de fuente/ícono sin cambiar cantidad de ítems) a
    Media (reestructurar a 4-5 ítems + "Más", **solo si** la evidencia lo
    sostiene).
- **Riesgo desktop**: **Bajo** para la recolección de evidencia (no toca
  código). Para acciones correctivas: Bajo si es solo ajuste de
  tamaños; Medio si implica reestructurar `NAV_ITEMS` (componente global,
  presente en todas las rutas y breakpoints).
- **Prioridad**: **P3** — explícitamente una tarea de **evaluación**, no
  de implementación. No se propone ocultar "Cambios"/"Cerca" tras un menú
  "Más" en este documento, a la espera de evidencia.

---

## 4. Tabla resumen

| ID | Tarea | Impacto UX | Complejidad | Riesgo desktop | Prioridad |
|---|---|---|---|---|---|
| P1-1 | Badges Álbum — tamaño táctil | Alto | Media | Medio | **P1** |
| P1-2 | Badges Faltantes — tamaño táctil | Alto | Baja | Bajo | **P1** |
| P1-3 | Badges Repetidas — tamaño táctil | Alto | Baja | Bajo | **P1** |
| P1-4 | Legibilidad números/badges/indicadores | Alto | Media | Bajo-Medio | **P1** |
| P1-5 | Uso de ancho disponible (grilla Álbum) | Alto (=P1-1) | Baja-Media | Medio | **P1** |
| P1-6 | Spacing y densidad visual | Medio | Baja | Bajo | **P1** |
| P2-1 | Dashboard — espacios muertos y jerarquía | Alto | Media | Bajo | **P2** |
| P2-2 | CTA principal para el coleccionista | Alto | Media | Bajo | **P2** |
| P3-1 | Bottom nav — evaluación de ergonomía | Por determinar | Baja (evaluación) | Bajo | **P3** |

---

## 5. Backlog secundario (sin cambios de prioridad, heredado de V1)

Estos ítems de V1 no fueron mencionados en el refocus y se mantienen como
backlog secundario, sin reclasificar:

- **A2 (V1)** — Acordeón para `CountryCard`: sigue siendo válido por
  "scroll excesivo de 49 tarjetas expandidas", pero **ya no se sostiene en
  la justificación de "contenido inaccesible"** (esa dependía de A1,
  retirado). Se mantiene como mejora de alcance grande/complejidad alta,
  a revisar después de P1/P2.
- **A4 (V1)** — Banderas pequeñas en `CountryCard`: impacto bajo, sin
  cambios.
- **A5 (V1)** — Legibilidad de `ProgressRing` (56px) en `CountryCard`:
  parcialmente cubierto por **P1-4** (indicadores de estado).
- **A6 (V1)** — "Pared roja" (exceso de color en estado FALTANTE): impacto
  medio, sin cambios; relacionado con **P1-4** en cuanto a legibilidad de
  indicadores de estado, pero es una decisión de color/contraste, no de
  tamaño.
- **D3 (V1)** — Grilla 2 columnas "Accesos rápidos" con celda vacía: se
  absorbe dentro de **P2-1** (eliminar espacios muertos del Dashboard).
- **D4 (V1)** — Affordance de scroll horizontal en tira de banderas: sin
  cambios, sigue siendo una mejora menor (P3/secundaria).

---

## 6. Resumen — qué hacer primero

La pregunta guía ("¿qué hace que el usuario necesite zoom?") se responde
con **P1-1 + P1-5** (badges del Álbum demasiado pequeños para el ancho real
disponible) como causa más probable y de mayor impacto, seguidas de cerca
por **P1-2/P1-3** (mismo problema en Faltantes/Repetidas, con menor
complejidad de implementación) y **P1-4** (legibilidad tipográfica
transversal). **P1-6** (spacing) es el quick win de menor esfuerzo dentro
del grupo P1.

P2 (Dashboard) y P3 (evaluación de bottom nav) quedan después, en ese
orden — P3 explícitamente como una tarea de **recolección de evidencia**,
no de rediseño, hasta que se confirme o descarte un problema real en la
navegación inferior.
