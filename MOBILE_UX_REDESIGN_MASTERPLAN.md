# Mobile UX Redesign Masterplan — StickerControl 2026

Auditoría de experiencia móvil basada **exclusivamente** en capturas reales
de Android físico (Chrome, `skillgames.com.ar/sticke...`, build con el fix
de ancho completo ya aplicado). No incluye análisis de código ni propuestas
de implementación — es un diagnóstico de diseño.

## 0. Evidencia analizada

| # | Captura | Pantalla | Hora |
|---|---|---|---|
| 1 | `1000666185.jpg` | Álbum — tope (Especiales del Mundial, Grupo A, Grupo B) | 10:34 |
| 2 | `1000666235.jpg` | Dashboard — tope (hero + accesos rápidos) | 11:40 |
| 3 | `1000666236.jpg` | Dashboard — scroll (accesos rápidos + espacio vacío + nav) | 11:41 |
| 4 | `1000666237.jpg` | Álbum — scroll medio (GER, CUW, CIV, ECU, NED) | 11:42 |

**Importante**: no se recibieron capturas dedicadas de **Faltantes**,
**Repetidas** ni un primer plano de la **navegación inferior**. Para esas
secciones, el análisis de las secciones 3, 4 y 5 es **parcial/inferido** a
partir de:
- el patrón de "badges en grilla" ya visible en Álbum (capturas 1 y 4),
  que es el mismo patrón visual que usan Faltantes/Repetidas;
- la navegación inferior, que **sí** es visible completa en las capturas 1
  y 3.

Se recomienda repetir la captura de Faltantes y Repetidas para confirmar o
ajustar el diagnóstico de esas secciones (marcado explícitamente abajo).

---

## 1. Dashboard (Inicio)

### Lo que muestran las capturas 2 y 3

- Tarjeta "hero" verde: título + anillo circular de progreso ("0.1% / 1 de
  980 pegadas"). El anillo ocupa ~40% del alto de la tarjeta; el resto es
  fondo verde liso.
- Tira horizontal de banderas pequeñas ("48 selecciones · 20 especiales").
- 3 tarjetas de stats en fila: Pegadas / Faltantes / Repetidas.
- Sección "Accesos rápidos": grilla 2 columnas con 5 tarjetas (Buscar,
  Álbum, Faltantes, Repetidas, Usuarios cerca) — la última fila queda con
  una celda vacía.
- **Debajo de "Usuarios cerca": un espacio vacío que ocupa más de la mitad
  de la pantalla restante**, hasta llegar a la navegación inferior.

### Problemas encontrados

| # | Problema | Evidencia | Prioridad |
|---|---|---|---|
| D1 | Espacio vacío masivo (~50% del viewport) entre "Accesos rápidos" y el nav inferior. La pantalla se siente "incompleta", como si faltara contenido o como si el diseño se pensó para una columna de altura fija (desktop) y no para el alto real de un teléfono. | Captura 3 | **Alta** |
| D2 | La tarjeta hero tiene mucho relleno vacío alrededor del anillo de progreso: el anillo es pequeño en relación al tamaño de la tarjeta verde que lo contiene. | Captura 2 | Media |
| D3 | La grilla "Accesos rápidos" de 2 columnas deja una celda vacía (5 elementos en grilla par) y, dentro de cada tarjeta, el ícono+texto ocupan ~40% del ancho disponible — el resto es espacio muerto. | Captura 2 | Media |
| D4 | La tira de banderas es muy delgada, las banderas son diminutas (~24px) y no hay ninguna pista visual (flechas, gradiente, dots) de que la tira es horizontalmente desplazable. | Captura 2 | Media |
| D5 | No hay una jerarquía clara de "siguiente acción". El dato más relevante para el usuario en este momento (979 faltantes) tiene el mismo peso visual que "0 repetidas" o que las tarjetas de accesos rápidos — nada le dice al usuario "esto es lo que importa ahora". | Capturas 2 y 3 | Alta |

### A/B/C/D — Dashboard

- **A) Desktop-first**: la grilla 2x3 de "Accesos rápidos" (patrón típico de
  panel de control de escritorio con tarjetas en mosaico) y la tarjeta hero
  con anillo circular pequeño dentro de un bloque grande de color sólido.
- **B) Debe cambiar de layout**: "Accesos rápidos" debería pasar de grilla
  2 columnas a **lista vertical de ancho completo** o **chips horizontales
  scrolleables** — en ambos casos elimina la celda vacía y agranda el área
  táctil de cada acceso.
- **C) Necesita versión móvil específica**: el bloque hero (ring +
  estadísticas) — en mobile convendría un formato más horizontal/compacto
  (barra de progreso lineal + número grande), liberando alto para otro
  contenido.
- **D) Pantalla a rediseñar completamente**: **sí**. El Dashboard necesita
  un nuevo propósito en mobile: no solo "mostrar estado", sino **dar una
  acción clara** ("Seguir completando el álbum", "Ver mis 979 faltantes").
  El espacio vacío de D1 es la señal más clara de que el contenido actual
  no fue pensado para el alto real de un celular.

---

## 2. Álbum

### Lo que muestran las capturas 1 y 4

- Pill verde de sección ("Especiales del Mundial", "Grupo A", "Grupo B").
- Por cada selección: tarjeta blanca con bandera pequeña (~24x16px),
  nombre del país, texto pequeño "X/20 pegadas" y "Y faltantes · Z
  repetidas", un anillo circular de progreso pequeño (~50px) a la derecha,
  y debajo **una grilla completa de 20 badges numerados** (más "00" para
  FIFA).
- En la captura 4 (GER, CUW, CIV, ECU, NED): se ven los números **1 a 10**
  en la primera fila y **20 suelto** en una segunda fila — **los números 11
  a 19 no son visibles** en la captura.
- El badge "6" de FIFA aparece en verde (pegada), todos los demás en rojo
  (faltante).

### Problemas encontrados

| # | Problema | Evidencia | Prioridad |
|---|---|---|---|
| A1 | **Números 11-19 no visibles** en las tarjetas GER/CUW/CIV/ECU/NED — solo se ven 1-10 y 20 suelto. El usuario no puede ver ni tocar esas figuritas sin algún gesto no evidente (scroll horizontal dentro de la tarjeta, si existe). Esto es un problema de **acceso al contenido**, no solo estético. | Captura 4 | **Alta** |
| A2 | Densidad extrema: 49 tarjetas (1 FIFA + 48 países), cada una con hasta 20 badges, todas expandidas y visibles simultáneamente. Para llegar al final del álbum el usuario debe scrollear una cantidad enorme de contenido repetitivo. | Capturas 1 y 4 | **Alta** |
| A3 | Badges numerados muy pequeños (~28px de alto aprox.), por debajo del tamaño táctil mínimo recomendado (~44-48px). Tocar un número específico entre 20 pegados unos a otros es propenso a error. | Capturas 1 y 4 | **Alta** |
| A4 | Banderas casi decorativas: a ~24x16px no se distinguen bien entre países con diseños similares (franjas verticales/horizontales de colores parecidos). | Captura 1 | Baja |
| A5 | Anillo de progreso por país (~50px) es difícil de leer en una pasada de scroll — para 48 países casi todos en "0%", el anillo no aporta información útil a ese tamaño y consume espacio. | Captura 1 | Media |
| A6 | "Pared roja": como casi todas las figuritas están en estado faltante, la pantalla es predominantemente roja. Visualmente correcto (rojo = falta), pero a esta escala (cientos de badges rojos) genera ruido visual y dificulta detectar las pocas verdes (pegadas) o amarillas (repetidas). | Capturas 1 y 4 | Media |

### A/B/C/D — Álbum

- **A) Desktop-first**: mostrar **las 49 tarjetas con sus 20 badges cada
  una, todas expandidas, todo el tiempo** es el patrón clásico de una tabla
  de escritorio "todo visible, scrollear con la rueda del mouse". En un
  teléfono esto se traduce en miles de píxeles de scroll vertical y badges
  diminutos.
- **B) Debe cambiar de layout**: la tarjeta de país debería tener **dos
  estados**: colapsado (resumen: bandera, nombre, progreso, contador
  faltantes/repetidas) y expandido (grilla de badges). Por defecto,
  colapsado. Esto resuelve A1, A2 y A3 de raíz: si la grilla de 20 badges
  solo se muestra para 1-2 países a la vez (los que el usuario abre), cada
  badge puede ser mucho más grande (full width / 5 por fila en vez de 10).
- **C) Necesita versión móvil específica**:
  - **Tarjeta de país** → componente acordeón (header siempre visible +
    contenido expandible).
  - **Grilla de badges** → en mobile, menos columnas (ej. 5 en vez de 10)
    y badges más grandes, para garantizar que **todas** las figuritas
    (incluidas 11-19) sean visibles sin scroll horizontal oculto.
  - **Indicador de sección** (Especiales, Grupo A, Grupo B...) → podría
    convertirse en un **selector/tab fijo** (sticky) para saltar
    directamente a un grupo sin scrollear los 48 países uno por uno.
- **D) Pantalla a rediseñar completamente**: **sí**. Es la pantalla con
  más contenido y la que más sufre el patrón "desktop reducido". Necesita
  un patrón de navegación por niveles (lista de países → detalle de país)
  o acordeones, no "todo expandido en una sola columna larga".

---

## 3. Faltantes ⚠️ (sin captura dedicada — análisis provisional)

No se recibió una captura de la pantalla "Faltantes". El análisis siguiente
se infiere a partir del patrón de badges visto en Álbum (capturas 1 y 4),
que según el código comparte el mismo tipo de componente visual (badges en
`flex-wrap`).

### Problemas esperables (a confirmar con captura real)

| # | Problema (hipótesis) | Prioridad |
|---|---|---|
| F1 | Si los badges de Faltantes tienen el mismo tamaño que los de Álbum (~28px), heredan el mismo problema de área táctil (A3). | Alta (a confirmar) |
| F2 | Si hay muchos países con muchas figuritas faltantes (caso actual: 979/980), la lista de badges por país puede ser muy larga — sin agrupar/colapsar, el scroll puede ser excesivo, similar a A2. | Media (a confirmar) |
| F3 | El botón "Copiar para WhatsApp" es una acción primaria — debe verificarse que tenga un tamaño y posición prominente en mobile (no compitiendo en altura con el resto del contenido). | Media (a confirmar) |

**Recomendación**: tomar 1-2 capturas de Faltantes (tope de pantalla y un
país con muchas figuritas faltantes) para completar este apartado con
evidencia real.

---

## 4. Repetidas ⚠️ (sin captura dedicada — análisis provisional)

Mismo caso que Faltantes: sin captura propia. Estructuralmente muy similar
a Faltantes (mismo tipo de badges, con indicador `(xN)` para cantidad de
repetidas).

### Problemas esperables (a confirmar con captura real)

| # | Problema (hipótesis) | Prioridad |
|---|---|---|
| R1 | Mismo problema de tamaño de badge que F1/A3, agravado porque el texto `N (xQ)` es más largo que un número solo — a tamaño ~28px, `"19 (x3)"` puede quedar muy comprimido o cortado. | Alta (a confirmar) |
| R2 | Si actualmente hay 0 repetidas (como muestra el Dashboard, captura 2), el estado vacío ("No tenés figuritas repetidas") es la única vista disponible para validar — habría que ver cómo se comunica ese estado vacío en mobile (¿ocupa toda la pantalla? ¿deja espacio vacío como en Dashboard, problema D1?). | Media (a confirmar) |

**Recomendación**: igual que Faltantes, tomar capturas reales (estado vacío
y, si es posible, con datos de prueba que tengan repetidas de 2 cifras).

---

## 5. Navegación inferior

### Lo que muestran las capturas 1 y 3

- Barra fija inferior de ancho completo (gracias al fix de layout ya
  aplicado).
- **7 destinos**: Inicio, Buscar, Álbum, Faltantes, Repetidas, Cambios,
  Cerca.
- Cada ítem: ícono pequeño + etiqueta de texto debajo, todos del mismo
  tamaño, item activo (Inicio/Álbum según pantalla) resaltado en verde.
- Los 7 ítems se reparten el ancho completo de la pantalla en partes
  iguales (~14% cada uno, aprox. 50-55px por ítem en un teléfono estándar).

### Problemas encontrados

| # | Problema | Evidencia | Prioridad |
|---|---|---|---|
| N1 | **7 destinos en la barra inferior** es muy por encima de lo recomendado (Material Design 3 sugiere 3-5 destinos para bottom navigation). Con 7, cada ítem es angosto, el ícono y la etiqueta quedan pequeños y el área táctil de cada ítem es menor a lo ideal. | Capturas 1 y 3 | **Alta** |
| N2 | Etiquetas de texto muy pequeñas (~9-10px estimado) — al límite de la legibilidad para texto en pantalla móvil (recomendado ≥ 11sp). Etiquetas como "Repetidas" y "Cambios" son largas para el espacio disponible (~50px). | Capturas 1 y 3 | Media |
| N3 | Distancia entre ítems mínima — los 7 ítems están prácticamente pegados unos a otros, sin "zona muerta" entre áreas táctiles, lo que aumenta el riesgo de tocar el destino vecino por error. | Capturas 1 y 3 | Media |
| N4 | Jerarquía: los 7 destinos tienen el mismo peso visual, pero no todos tienen la misma frecuencia de uso esperada (p.ej. "Cerca"/"Usuarios cerca" probablemente se usa mucho menos que "Álbum" o "Faltantes"). No hay distinción entre acciones primarias y secundarias. | Capturas 1 y 3 | Media |

### A/B/C/D — Navegación inferior

- **A) Desktop-first**: una barra de navegación con 7 ítems es típica de un
  **menú lateral o superior de escritorio** (donde hay espacio horizontal
  de sobra) trasladado tal cual a una bottom nav móvil.
- **B) Debe cambiar de layout**: reducir a **4-5 destinos primarios** en la
  barra (ej. Inicio, Álbum, Faltantes, Repetidas/Cambios, Buscar) y mover el
  resto (ej. "Cerca", "Cambios" si no son de uso frecuente) a un quinto
  ítem "Más" que abre un menú, o integrarlos como accesos dentro de otras
  pantallas (ej. "Cerca" como ícono en el header del Álbum).
- **C) Necesita versión móvil específica**: la bottom nav en sí — íconos
  más grandes, etiquetas más cortas o solo-ícono con etiqueta visible
  únicamente en el ítem activo (patrón común en Android/iOS).
- **D) Pantalla a rediseñar completamente**: no es una "pantalla", pero el
  **componente** sí debería revisarse como parte del rediseño general,
  porque está presente en todas las pantallas y su densidad actual
  contribuye a la sensación general "todo es chiquito".

---

## 6. Comparación contra Material Design 3 / Android UX Guidelines / PWAs modernas

| Criterio | Guideline (MD3 / Android / PWA) | Lo observado en las capturas | Brecha |
|---|---|---|---|
| Tamaño mínimo de área táctil | ≥ 48dp x 48dp (Android), ≥ 44px (WCAG) | Badges de figuritas ~28px, ítems de bottom nav ~50px de ancho pero con ícono+texto muy comprimidos | Badges muy por debajo del mínimo; bottom nav al límite |
| Cantidad de destinos en bottom navigation | 3-5 destinos recomendados | 7 destinos | Excede el máximo recomendado |
| Uso del espacio vertical en mobile | El contenido debe adaptarse al alto del viewport (no dejar bloques de "aire" sin función) | Dashboard deja ~50% de la pantalla vacía tras "Accesos rápidos" | Brecha alta — patrón típico de contenido pensado para una columna de alto fijo (desktop) |
| Densidad de información / listas largas | Patrones de "progressive disclosure": acordeones, listas colapsadas, paginación o virtualización para listas largas | Álbum muestra 49 tarjetas x hasta 20 badges, todo expandido simultáneamente | Brecha alta — necesita colapsar/expandir |
| Jerarquía visual / color con propósito | El color debe dirigir la atención a lo más relevante; evitar "ruido" de un solo color dominante | Predominancia de rojo (faltantes) en casi toda la pantalla del Álbum | Riesgo de "ceguera" al color por sobreuso |
| Elementos scrolleables horizontales | Deben tener affordance visual (gradiente de borde, indicador de páginas, "peek" del siguiente elemento) | Tira de banderas sin ninguna pista de scroll horizontal | Brecha media |
| Accesibilidad de contenido (todo visible sin gestos ocultos) | Todo el contenido relevante debe ser alcanzable con scroll vertical estándar | Números 11-19 no visibles en tarjetas de país (Álbum) | Brecha alta — posible contenido inalcanzable |

---

## 7. Mockups textuales — cómo debería verse cada pantalla en mobile

### 7.1 Dashboard

```
┌─────────────────────────────────────┐
│  StickerControl 2026                 │
│  ┌─────────────────────────────────┐│
│  │  Mi álbum del Mundial            ││
│  │  ▓▓▓▓░░░░░░░░░░░░░░░░░  0.1%     ││  ← barra lineal, no anillo
│  │  1 / 980 pegadas                 ││
│  └─────────────────────────────────┘│
│                                       │
│  [ Pegadas: 1 ] [Faltantes:979][Rep:0]│  ← 3 stats, fila compacta
│                                       │
│  ▶  979 figuritas te faltan          │  ← CTA primaria, full width
│     Ver lista de faltantes      →    │
│                                       │
│  Accesos rápidos                     │
│  ──────────────────────────────────  │
│  🔍  Buscar una figurita          →  │  ← lista vertical full width,
│  📖  Ver álbum completo           →  │     un ítem por fila, alto
│  🔁  Mis repetidas (0)             → │     táctil ≥48px cada uno
│  📍  Usuarios cerca                → │
│  ──────────────────────────────────  │
│                                       │
│  🏳 Selecciones (48) · Especiales (20)│  ← tira de banderas con
│  [MEX][RSA][KOR][CZE][CAN] ›››        │     indicador de scroll (›››)
│                                       │
│  (sin espacio vacío residual:         │
│   el contenido llena el viewport)     │
└─────────────────────────────────────┘
│ Inicio  Álbum  Faltantes  Más   │  ← bottom nav 4-5 ítems
```

### 7.2 Álbum (vista lista, colapsado por defecto)

```
┌─────────────────────────────────────┐
│  Álbum                       🔍 📍   │  ← buscador / "cerca" en header
│  [Especiales][Grupo A][Grupo B]...   │  ← tabs/chips fijos (sticky) para
│  ──────────────────────────────────  │     saltar de sección
│                                       │
│  Especiales del Mundial               │
│  ┌─────────────────────────────────┐│
│  │ 🟦FIFA  Especiales FIFA WC 2026  ││
│  │ ▓░░░░░░░░░░░░░░░  5%   1/20  ▾  ││  ← header colapsado: barra +
│  └─────────────────────────────────┘│     porcentaje + contador + ▾
│                                       │
│  Grupo A                              │
│  ┌─────────────────────────────────┐│
│  │ 🇲🇽 México (MEX)                 ││
│  │ ▓░░░░░░░░░░░░░░░  0%  0/20   ▾  ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ 🇿🇦 South Africa (RSA)            ││
│  │ ░░░░░░░░░░░░░░░░  0%  0/20   ▾  ││
│  └─────────────────────────────────┘│
│   ... (un renglón por país, scroll   │
│        corto y predecible)           │
└─────────────────────────────────────┘
```

### 7.3 Álbum — tarjeta de país EXPANDIDA (al tocar ▾)

```
┌─────────────────────────────────────┐
│ 🇩🇪 Germany (GER)                     │
│ ▓░░░░░░░░░░░░░░░░░  0%   0/20    ▴   │
│                                       │
│  (1) (2) (3) (4) (5)                 │  ← 5 por fila (no 10), badges
│  (6) (7) (8) (9) (10)                │     más grandes (~48px),
│ (11)(12)(13)(14)(15)                  │     TODOS los números visibles
│ (16)(17)(18)(19)(20)                  │     sin scroll horizontal oculto
└─────────────────────────────────────┘
```

### 7.4 Faltantes / Repetidas (estructura propuesta, basada en patrón 7.3)

```
┌─────────────────────────────────────┐
│  Faltantes (979)                     │
│  ┌─────────────────────────────────┐│
│  │ 📋 Copiar para WhatsApp          ││  ← CTA full width, alto ≥48px
│  └─────────────────────────────────┘│
│                                       │
│  Especiales del Mundial (FWC)         │
│  (00)(1)(2)(3)(4)                     │  ← misma grilla de 5 por fila
│  (5)(6)(7)(8)(9)                      │     que en Álbum expandido,
│  (10)(11)(12)...(19)                  │     badges ≥48px
│                                       │
│  México (MEX)                         │
│  (1)(2)(3)(4)(5) ...                  │
│   ... (agrupado por país/sección,     │
│        igual jerarquía que Álbum)     │
└─────────────────────────────────────┘
```

### 7.5 Navegación inferior (propuesta de reducción)

```
┌─────────────────────────────────────┐
│   🏠      📖       ⚠️       •••     │
│ Inicio   Álbum   Faltantes   Más     │
└─────────────────────────────────────┘
                                  │
                                  ▼ (al tocar "Más")
                         ┌─────────────────┐
                         │ 🔍 Buscar        │
                         │ 🔁 Repetidas     │
                         │ 🔄 Cambios       │
                         │ 📍 Cerca         │
                         └─────────────────┘
```

---

## 8. Resumen de prioridades

| Prioridad | Hallazgos |
|---|---|
| **Alta** | D1 (espacio vacío Dashboard), D5 (sin jerarquía/CTA), A1 (números 11-19 no visibles), A2 (49 tarjetas expandidas = scroll excesivo), A3 (badges < área táctil mínima), N1 (7 destinos en bottom nav) |
| **Media** | D2 (hero con relleno vacío), D3 (grilla 2 cols con celda muerta), D4 (tira de banderas sin affordance), A5 (anillos de progreso poco legibles), A6 ("pared roja"), N2 (etiquetas muy pequeñas), N3 (poco espacio entre ítems de nav), N4 (sin jerarquía primaria/secundaria en nav) |
| **Baja** | A4 (banderas poco distinguibles) |
| **A confirmar con capturas** | F1-F3 (Faltantes), R1-R2 (Repetidas) |

---

## 9. Conclusión

Las capturas confirman el diagnóstico que motivó este pedido: **la app ya
es técnicamente correcta (HTTPS, build, viewport, ancho completo) pero la
experiencia se "siente" como una página de escritorio reducida** porque:

1. El **contenido y los componentes no cambian de forma** entre desktop y
   mobile — solo cambia el ancho del contenedor. Grillas de 10 columnas,
   anillos de progreso diminutos, banderas chicas y una bottom nav de 7
   ítems son decisiones de densidad pensadas para una pantalla ancha.
2. El **Dashboard tiene contenido "de altura fija"** que no llena pantallas
   altas (típico de móviles modernos), dejando vacíos que rompen la
   sensación de "app nativa".
3. El **Álbum no tiene un mecanismo de progressive disclosure** (colapsar/
   expandir), por lo que toda la información de 49 países se renderiza
   siempre, generando scroll excesivo y, en al menos un caso observado,
   contenido (figuritas 11-19) que no es visible/alcanzable.
4. La **navegación inferior** replica una cantidad de destinos pensada para
   un menú de escritorio, no para una bottom nav.

Este documento es solo diagnóstico — no se modificó código ni se proponen
clases o implementaciones. El siguiente paso natural (si se aprueba) sería
priorizar 2-3 hallazgos de prioridad **Alta** para una segunda fase de
diseño detallado (wireframes de mayor fidelidad) antes de tocar código.
