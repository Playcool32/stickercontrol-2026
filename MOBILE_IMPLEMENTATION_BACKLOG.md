# Mobile Implementation Backlog — StickerControl 2026

Fuente única: `MOBILE_UX_REDESIGN_MASTERPLAN.md`.

Este documento traduce cada hallazgo de la auditoría UX en un ítem técnico
planificable. **No incluye código ni implementación** — solo planificación
(componente, archivo, complejidad, impacto, estimación, riesgo).

## 0. Criterio de priorización

- **P1** = Impacto UX **Alto** + Complejidad **Baja** → mayor mejora con
  menor esfuerzo y menor riesgo. Hacer primero.
- **P2** = Impacto UX **Alto** + Complejidad **Media** → mejoras grandes
  que requieren más trabajo/testing, pero siguen siendo de alto valor.
- **Fase posterior** = Impacto **Alto** + Complejidad **Alta** → fuera de
  P1-P3 por definición (no son "quick wins" ni "mejoras medias"). Requieren
  diseño detallado previo antes de estimarse en serio. Se listan aparte para
  no perderlas de vista.
- **P3** = Mejoras estéticas / impacto medio-bajo, cualquier complejidad.

Dentro de cada bloque, los ítems están ordenados por menor
esfuerzo/riesgo primero.

---

## 1. Tabla maestra

| ID | Hallazgo (masterplan) | Componente | Archivo(s) | Complejidad | Impacto UX | Estimación | Riesgo desktop | Prioridad |
|---|---|---|---|---|---|---|---|---|
| A1 | Números 11-19 no visibles en tarjetas de país | `CountryCard` (grilla de badges) | `frontend/src/pages/Album.jsx` (línea ~125, `grid-cols-8 sm:grid-cols-10`) | Baja | Alto | 1-2h | Medio | **P1** |
| F1/R1 | Badges de Faltantes/Repetidas por debajo del área táctil mínima | badges `<span>` | `frontend/src/pages/Missing.jsx`, `frontend/src/pages/Duplicates.jsx` | Baja | Alto (a confirmar) | 1-2h | Bajo | **P1** |
| A3 | Badges de figuritas (Álbum) por debajo del área táctil mínima (~32px) | `CountryCard` (grilla de badges) | `frontend/src/pages/Album.jsx` | Media (depende de A1) | Alto | 3-5h | Medio | **P2** |
| D1/D5 | Espacio vacío masivo en Dashboard + sin jerarquía/CTA | Página Dashboard (estructura general) | `frontend/src/pages/Dashboard.jsx` | Media | Alto | 4-6h | Bajo | **P2** |
| N1 | 7 destinos en bottom nav (excede recomendación MD3) | `Layout` (nav inferior) + nuevo componente "Más" | `frontend/src/components/Layout.jsx` (+ nuevo archivo, ej. `MoreMenu.jsx`) | Media | Alto | 4-8h | Medio | **P2** |
| A2 | 49 tarjetas con grilla completa expandida siempre (scroll excesivo) | `CountryCard` → acordeón | `frontend/src/pages/Album.jsx` | Alta | Alto | 1-2 días | Medio | Fase posterior |
| N2/N3/N4 | Etiquetas pequeñas, poco espacio, sin jerarquía primaria/secundaria | `Layout` (nav inferior) | `frontend/src/components/Layout.jsx` | — (subsumido en N1) | — | — | — | (incluido en N1) |
| D3 | Grilla 2 columnas "Accesos rápidos" con celda muerta | `QuickLink` grid | `frontend/src/pages/Dashboard.jsx` (línea ~108) | Baja | Medio | 1h | Bajo | P3 |
| D2 | Hero card con mucho relleno vacío alrededor del anillo | Hero card + `ProgressRing` | `frontend/src/pages/Dashboard.jsx` (línea ~56-69) | Baja | Medio | 1h | Bajo | P3 |
| D4 | Tira de banderas sin affordance de scroll horizontal | Flag strip | `frontend/src/pages/Dashboard.jsx` (línea ~78-94) | Baja | Bajo-Medio | 1h | Bajo | P3 |
| A6 | "Pared roja" — exceso de color en estado FALTANTE | `STATUS_COLOR` (local a CountryCard) | `frontend/src/pages/Album.jsx` (línea ~9-14) | Baja-Media | Medio | 1-2h | Medio (si se toca token global) / Bajo (si se limita a `Album.jsx`) | P3 |
| A5 | Anillos de progreso por país poco legibles a 56px | `ProgressRing` (uso en `CountryCard`) | `frontend/src/pages/Album.jsx`, posible ajuste en `ProgressRing.jsx` | Baja-Media | Medio | 1-2h | Bajo | P3 |
| A4 | Banderas pequeñas, poco distinguibles | `img` bandera en `CountryCard` | `frontend/src/pages/Album.jsx` | Baja | Bajo | 30min | Bajo | P3 |
| F2/F3, R2 | Agrupación/CTA de Faltantes/Repetidas (pendiente confirmar) | `Missing.jsx` / `Duplicates.jsx` | `frontend/src/pages/Missing.jsx`, `frontend/src/pages/Duplicates.jsx` | A definir | A confirmar | A definir | A definir | Pendiente capturas |

---

## 2. P1 — Hacer primero (alto impacto, baja complejidad, bajo riesgo)

### P1.1 — A1: Garantizar que las 20 figuritas de cada país sean visibles sin overflow oculto

- **Componente**: `CountryCard` (grilla de badges numerados dentro de cada
  tarjeta de país/especiales).
- **Archivo**: `frontend/src/pages/Album.jsx`, línea ~125 — clase actual
  `grid grid-cols-8 gap-1 sm:grid-cols-10`.
- **Complejidad**: **Baja**. Es un cambio de clases de grid (número de
  columnas y/o breakpoint) en un único componente (`CountryCard`), que se
  reutiliza para las 49 tarjetas — un solo cambio se propaga a todas.
- **Impacto UX**: **Alto**. Resuelve un caso donde contenido (figuritas
  11-19) podría no ser alcanzable por el usuario — el hallazgo más crítico
  de toda la auditoría desde el punto de vista funcional, no solo estético.
- **Estimación**: 1-2h, incluyendo:
  - 30min de investigación dirigida (reproducir en el celular real con
    distintos `country_code`, confirmar si es overflow horizontal real o
    un glitch de repintado de Chrome al hacer scroll).
  - 30-60min de ajuste de clases + verificación visual en el dispositivo.
- **Riesgo de romper desktop**: **Medio**. El breakpoint actual `sm:`
  (640px) queda **dentro** del rango "mobile" según el fix de layout ya
  aplicado (que usa `md:` = 768px como frontera mobile/desktop). Cualquier
  ajuste debe revisarse contra ambos breakpoints (`sm` y `md`) para no
  generar un estado intermedio (640px-768px) con una configuración de
  columnas distinta a la de <640px y a la de ≥768px. Mitigación: probar en
  3 anchos (ej. 375px, 700px, 1024px) antes de cerrar el cambio.

### P1.2 — F1/R1: Agrandar badges de Faltantes y Repetidas

- **Componente**: badges `<span>` dentro de `country.numbers.map(...)` /
  `country.items.map(...)`.
- **Archivos**: `frontend/src/pages/Missing.jsx` (línea ~51-58),
  `frontend/src/pages/Duplicates.jsx` (línea ~51-61).
- **Complejidad**: **Baja**. Son los mismos dos archivos ya tocados en el
  fix del código "00" — cambio puntual de padding/tamaño de fuente en un
  `<span>` dentro de un `flex flex-wrap`, sin tocar lógica ni datos.
- **Impacto UX**: **Alto** (asumido por similitud con A3/badges de Álbum;
  **pendiente confirmar con capturas reales** de Faltantes/Repetidas, ver
  masterplan §3-4).
- **Estimación**: 1-2h (ambos archivos, por la similitud estructural).
- **Riesgo de romper desktop**: **Bajo**. `flex-wrap` se adapta solo;
  agrandar el badge simplemente reduce la cantidad por fila, tanto en
  mobile como en desktop, sin romper el layout.
- **Nota**: este ítem se puede ejecutar en la misma sesión que P1.1 (mismo
  tipo de cambio — "badges más grandes para mejor toque"), pero son
  componentes y archivos independientes, sin dependencia entre sí.

---

## 3. P2 — Alto impacto, complejidad media

### P2.1 — A3: Badges de figuritas en Álbum con área táctil ≥ 44-48px

- **Componente**: `CountryCard` (grilla de badges).
- **Archivo**: `frontend/src/pages/Album.jsx` (mismo bloque que A1, línea
  ~125-136 — clase `h-8` de cada botón + columnas del grid).
- **Complejidad**: **Media**. Depende del resultado de A1 (P1.1): una vez
  fijada la cantidad de columnas que garantiza visibilidad de 1-20,
  agrandar el alto de cada botón (`h-8` → ~`h-11`/`h-12`) aumenta
  proporcionalmente el alto de cada una de las 49 tarjetas. Requiere
  recalcular el balance columnas/tamaño para no generar tarjetas
  excesivamente altas, y revisar visualmente varias tarjetas (especiales,
  grupo con menos faltantes, grupo con 20/20 faltantes) para validar que el
  badge "00" y los de 2 cifras (10-20) se vean bien con el nuevo tamaño.
- **Impacto UX**: **Alto**. Es el ítem que más directamente ataca "tocar
  una figurita específica es propenso a error" (A3 del masterplan).
- **Estimación**: 3-5h (incluye P1.1 ya resuelto como prerequisito, ajuste
  de tamaño, y verificación visual en ~6-8 tarjetas representativas más el
  modal de detalle que se abre al tocar un badge).
- **Riesgo de romper desktop**: **Medio**. Agrandar badges incrementa la
  altura total de cada tarjeta y, por lo tanto, el alto total del Álbum —
  en desktop esto se traduce en más scroll vertical (aceptable) pero debe
  verificarse que la columna de 672px (`md:max-w-2xl`) sigue viéndose
  proporcionada y no "vacía" a los costados con badges más grandes.

### P2.2 — D1/D5: CTA principal + reorganización del Dashboard

- **Componente**: página Dashboard completa (estructura/orden de
  secciones).
- **Archivo**: `frontend/src/pages/Dashboard.jsx`.
- **Complejidad**: **Media**. No requiere nuevos endpoints (el dato clave,
  `summary.faltantes`, ya está disponible en el estado actual). Sí requiere:
  - Diseñar y construir un nuevo bloque "CTA" (ej. tarjeta destacada
    "979 figuritas te faltan → Ver lista", enlazando a `/faltantes`).
  - Reordenar/condensar las secciones existentes (hero, stats, accesos
    rápidos, tira de banderas) para que el conjunto llene el viewport sin
    dejar el vacío observado en la captura 3 del masterplan.
  - Esto puede solaparse con D2/D3/D4 (mismos archivos, mismas secciones) —
    conviene planificarlos juntos aunque se listen por separado.
- **Impacto UX**: **Alto**. Ataca dos hallazgos "Alta" del masterplan a la
  vez (espacio vacío + falta de jerarquía/CTA), que son los que más
  refuerzan la sensación de "página de escritorio reducida".
- **Estimación**: 4-6h (incluye el nuevo componente CTA + reorganización +
  verificación de que ya no queda espacio vacío significativo en un
  teléfono real).
- **Riesgo de romper desktop**: **Bajo**. El Dashboard en desktop ya tiene
  más alto de columna relativo (672px de ancho vs. mobile full-width), por
  lo que agregar contenido (la CTA) y reordenar secciones existentes no
  debería generar problemas — en el peor caso, un poco más de scroll en
  desktop también, lo cual es aceptable.

### P2.3 — N1 (+ N2/N3/N4): Reducir bottom nav a 4-5 destinos + menú "Más"

- **Componente**: `Layout` (nav inferior) + nuevo componente de menú
  ("Más").
- **Archivos**:
  - `frontend/src/components/Layout.jsx` (líneas 13-21 `NAV_ITEMS`, y
    30-60 el render del `<nav>` con `grid-cols-7`).
  - Nuevo archivo, ej. `frontend/src/components/MoreMenu.jsx` (bottom
    sheet o menú desplegable con los destinos secundarios) — puede
    reutilizar el patrón visual ya existente de
    `StickerDetailModal.jsx` (overlay + panel `items-end` en mobile).
- **Complejidad**: **Media**. Componentes nuevos pero acotados:
  - Decidir qué 4-5 destinos quedan fijos (ej. Inicio, Álbum, Faltantes,
    Repetidas/Buscar) y cuáles van a "Más" (ej. Cambios, Cerca, y el que
    no entre).
  - Construir el menú "Más" (overlay + lista de accesos).
  - Lógica de estado activo: si la ruta actual es una de las que están
    dentro de "Más" (ej. `/cerca`), el ítem "Más" debe mostrarse resaltado
    como activo — esto requiere comparar `location.pathname` contra la
    lista de rutas "secundarias".
  - Esto subsume **N2** (etiquetas pequeñas — con 5 ítems en vez de 7 hay
    más espacio para texto legible), **N3** (poco espacio entre ítems — se
    resuelve solo al haber menos ítems) y **N4** (jerarquía primaria/
    secundaria — es justamente lo que separa nav fija vs. menú "Más").
- **Impacto UX**: **Alto**. La bottom nav está presente en **todas** las
  pantallas — es el componente con mayor "superficie de exposición" de
  toda la app.
- **Estimación**: 4-8h (incluye diseño del menú "Más", lógica de estado
  activo, y verificación de que las 7 rutas siguen siendo alcanzables —
  5 directas + 2 dentro de "Más").
- **Riesgo de romper desktop**: **Medio**. Es un componente global
  (`Layout.jsx`) usado en todas las rutas/ambos breakpoints — cualquier
  error de lógica de "activo" o de routing afecta toda la app, en mobile y
  desktop. Mitigación: probar navegación completa (las 7 rutas, en los dos
  breakpoints) antes de cerrar el cambio, igual que se hizo con
  `vite preview` en el fix de layout anterior.

---

## 4. Fase posterior — Alto impacto, alta complejidad (requiere diseño previo)

### A2: Convertir `CountryCard` en acordeón (colapsado por defecto)

- **Componente**: `CountryCard` (Álbum) → nuevo componente con estado
  expandido/colapsado.
- **Archivo**: `frontend/src/pages/Album.jsx` (reestructuración del
  componente `CountryCard` y de cómo `Album` renderiza las 49 tarjetas).
- **Complejidad**: **Alta**:
  - Estado de expansión por tarjeta (49 tarjetas) — decidir si es estado
    local por tarjeta, un set de "IDs expandidos" en `Album`, o
    expansión exclusiva (acordeón clásico, solo 1 abierta a la vez).
  - Header colapsado necesita rediseño (resumen: bandera + nombre +
    progreso + contador, sin la grilla de 20 badges).
  - Transición/animación de expandir-colapsar (afecta percepción de
    calidad — si se hace sin animación puede sentirse "brusco").
  - Accesibilidad: rol/aria-expanded, navegación por teclado (aunque el
    foco de la app es mobile, no debería romperse en desktop).
  - Interacción con `StickerDetailModal`: el flujo actual es
    tarjeta → grilla visible → tocar badge → modal. Con acordeón, el flujo
    pasa a ser tarjeta colapsada → tocar para expandir → grilla visible →
    tocar badge → modal. Un paso adicional que debe sentirse natural, no
    como una traba.
- **Impacto UX**: **Alto**. Es el cambio que más reduce el scroll total del
  Álbum (de "49 tarjetas x 20 badges siempre visibles" a "49 resúmenes +
  grilla solo donde el usuario la pide") y resuelve A2 del masterplan de
  raíz.
- **Estimación**: **1-2 días** (incluye diseño de la tarjeta colapsada,
  implementación del estado, animación básica, y testing manual de las 49
  tarjetas + flujo de modal).
- **Riesgo de romper desktop**: **Medio**. Cambia el comportamiento de
  navegación del Álbum **en ambos breakpoints** (hoy en desktop el Álbum
  también muestra las 49 tarjetas expandidas — "funciona" pero es largo).
  Un acordeón colapsado-por-defecto es un cambio de comportamiento, no solo
  de estilo, y afecta la experiencia desktop actual (que el usuario
  describió como "funciona bien"). Se recomienda **validar con el usuario
  si el comportamiento colapsado-por-defecto debe aplicar también en
  desktop, o solo por debajo de `md:` (768px)** antes de implementar — esta
  es una decisión de producto, no solo técnica.

> **Por qué queda fuera de P1-P3**: A2 tiene el impacto más alto de todo el
> backlog junto con A1, pero su complejidad/riesgo es desproporcionadamente
> mayor que cualquier otro ítem. Forzarlo dentro de P1-P3 distorsionaría la
> lectura de "qué hacer primero con el menor riesgo posible". Se recomienda
> abordarlo en una iteración separada, después de P1 y P2, e idealmente con
> un mockup de alta fidelidad de la tarjeta colapsada antes de tocar código.

---

## 5. P3 — Mejoras estéticas / impacto medio-bajo

Ordenadas por esfuerzo (menor primero) — son candidatas a agruparse en una
misma sesión de trabajo junto con P2.2 (Dashboard), ya que varias tocan el
mismo archivo.

| ID | Cambio | Archivo | Complejidad | Impacto | Estimación | Riesgo |
|---|---|---|---|---|---|---|
| A4 | Banderas un poco más grandes en `CountryCard` | `Album.jsx` | Baja | Bajo | 30min | Bajo |
| D2 | Reducir relleno vacío del hero card (Dashboard) — anillo más proporcionado al contenedor, o layout más horizontal | `Dashboard.jsx` | Baja | Medio | 1h | Bajo |
| D3 | "Accesos rápidos": de grilla 2 columnas a lista vertical de ancho completo (o chips horizontales) | `Dashboard.jsx` | Baja | Medio | 1h | Bajo |
| D4 | Agregar affordance de scroll horizontal a la tira de banderas (gradiente/fade en el borde) | `Dashboard.jsx` | Baja | Bajo-Medio | 1h | Bajo |
| A5 | Revisar tamaño/legibilidad de `ProgressRing` en `CountryCard` (56px) — posible aumento o cambio a barra lineal | `Album.jsx` (uso), posible ajuste en `ProgressRing.jsx` | Baja-Media | Medio | 1-2h | Bajo |
| A6 | Reducir "pared roja": cambiar el estilo del estado FALTANTE en `STATUS_COLOR` de `Album.jsx` (de rojo sólido a, ej., fondo neutro + borde/texto rojo) | `Album.jsx` (mapa local `STATUS_COLOR`, **no** tocar `tailwind.config.js`) | Baja-Media | Medio | 1-2h | Bajo si se limita a `Album.jsx`; **Medio si se decide cambiar el token `faltante` global** (afectaría también `StatusBadge.jsx`, `StickerCard.jsx`, `Missing.jsx`, `Duplicates.jsx`, `Nearby.jsx`) |

---

## 6. Pendiente — Faltantes / Repetidas (requiere capturas)

F2, F3, R1 (parcialmente cubierto por P1.2), R2 quedan sin estimar de forma
completa porque el masterplan los marcó como "a confirmar con captura
real". Una vez disponibles esas capturas, se pueden incorporar como ítems
P1/P2/P3 siguiendo el mismo formato de esta tabla — la expectativa, dado que
ambas pantallas comparten el mismo patrón de badges que Álbum, es que la
mayoría de los ajustes adicionales (si los hay) sean de **complejidad
Baja**, similar a P1.2.

---

## 7. Roadmap recomendado

Orden sugerido para maximizar mejora de experiencia móvil con el menor
riesgo, agrupando por sesión de trabajo:

1. **Sesión 1 (P1, ~3-4h)**: A1 (P1.1) + F1/R1 (P1.2). Ambos son cambios
   acotados, de bajo riesgo, en archivos pequeños (`Album.jsx`,
   `Missing.jsx`, `Duplicates.jsx`), y atacan directamente los dos
   hallazgos de "contenido no alcanzable / no tocable" — el tipo de
   problema más grave desde el punto de vista funcional.
2. **Sesión 2 (P2.1, ~3-5h)**: A3 — agrandar badges del Álbum, ahora que
   A1 ya definió la grilla correcta. Requiere la verificación visual más
   extensa de este grupo (49 tarjetas), por eso va después de A1, no junto.
3. **Sesión 3 (P2.2 + P3 del Dashboard, ~5-7h)**: D1/D5 (CTA + reorden) +
   D2/D3/D4 (mismos archivos, se aprovecha el contexto). Es la sesión que
   más cambia la "primera impresión" de la app.
4. **Sesión 4 (P2.3, ~4-8h)**: N1/N2/N3/N4 — bottom nav. Se deja para
   después de las anteriores porque es un componente global (mayor
   superficie de riesgo) y conviene tocarlo cuando el resto de las
   pantallas ya esté estabilizado, para testear navegación contra el
   resultado final de Dashboard/Álbum.
5. **Sesión 5 (P3 restante, ~3-5h)**: A4, A5, A6 — pulidos visuales de
   Álbum.
6. **Fase posterior (A2, 1-2 días, con decisión de producto previa)**:
   acordeón en Álbum. Requiere mockup de alta fidelidad y una decisión
   explícita sobre si el comportamiento colapsado aplica también a
   desktop.

**Resumen de "qué hacer primero"**: P1.1 (A1) y P1.2 (F1/R1) son los dos
únicos ítems con impacto Alto, complejidad Baja y riesgo Bajo/Medio
acotado a archivos pequeños — son el punto de partida recomendado.
