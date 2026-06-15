# Root Cause Analysis — "MOBILE P1 VALIDATION FAILED"

> Alcance de este informe: **diagnóstico únicamente**. No se modificó código
> de la aplicación. Las únicas acciones realizadas fueron lectura de
> archivos, lectura de `git log`, verificación de timestamps y revisión de
> las capturas reales aportadas (carpeta `imagenes/v2`).

---

## ACTUALIZACIÓN — Capturas reales post-P1 (`imagenes/v2`)

Se recibieron 5 capturas nuevas (`1000666274.jpg` a `1000666278.jpg`),
tomadas a las **12:34–12:35**, es decir **4-5 minutos después** del commit
`ee0b5a7` (12:30). A diferencia del primer lote, **estas sí son posteriores
a P1** y constituyen evidencia válida.

### Qué muestran

| Captura | Pantalla | Observación clave |
|---|---|---|
| `1000666274.jpg` | Dashboard | Hero verde + tira de banderas + 3 stats + "Accesos rápidos" 2 col + espacio vacío grande — igual que en el masterplan original |
| `1000666275.jpg` | Buscar | Pantalla vacía con input de búsqueda — sin cambios |
| `1000666276.jpg` | Álbum | **Cada tarjeta de país muestra sus 20 badges en 2 filas de 10** (ej. FIFA: `00 1 2 3 4 5 6 7 8 9` / `10..19`; México: `1..10` / `11..20`) |
| `1000666277.jpg` | Faltantes | **México (MEX) muestra 19 badges en una sola fila** (`1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19`) y `20` en la fila siguiente — badges pequeños, `px`/`py` chicos |
| `1000666278.jpg` | Repetidas | Estado vacío ("No tenés figuritas repetidas") — sin badges para evaluar |

### El hallazgo central

Las clases de P1 para Álbum son `grid-cols-5 gap-2` (mobile, <768px) y
`md:grid-cols-10 md:gap-1` (≥768px). Las clases de Faltantes/Repetidas son
`gap-2` + badge `px-3 py-3 text-sm font-bold` (mobile) y `md:gap-1 md:px-2
md:py-1 md:text-xs md:font-semibold` (≥768px).

**Las capturas muestran inequívocamente las variantes `md:` (≥768px)**:
grilla de 10 columnas en Álbum, y en Faltantes 19 badges chicos
(`px-2 py-1 text-xs`) entrando en una sola fila — algo que solo es posible
si el contenedor tiene **varios cientos de píxeles de ancho CSS
disponibles** (19 badges de ~35-40px + gaps ≈ 700-750px).

Esto es importante incluso **sin saber si el `dist/` desplegado incluye
P1**, porque:

- Si el `dist/` desplegado es **anterior a P1** (clases viejas
  `grid-cols-8 gap-1 sm:grid-cols-10`): ver `grid-cols-10` también requiere
  viewport ≥640px (`sm:`).
- Si el `dist/` desplegado **incluye P1** (clases nuevas
  `grid-cols-5 gap-2 md:grid-cols-10 md:gap-1`): ver `grid-cols-10` requiere
  viewport ≥768px (`md:`).

**En ambos casos, el ancho de viewport CSS efectivo en el dispositivo es
≥640-768px.** Un teléfono Android en orientación vertical, con el
`<meta name="viewport" content="width=device-width, initial-scale=1.0">`
que efectivamente está presente en `frontend/index.html`, tiene un viewport
CSS de **~360-412px** — muy por debajo de ambos umbrales.

### Causa raíz real (independiente del deploy)

La conclusión más simple y consistente con **las 6 observaciones del
usuario a la vez** es: **el navegador está sirviendo la página en modo
"Sitio de escritorio" (Request Desktop Site) o con un zoom/viewport forzado
a escala de escritorio**, no en modo móvil normal.

Esto, por sí solo, explica todo lo reportado **sin necesidad de que el
código de P1 esté roto**:

- El navegador ignora (o Chrome sobreescribe) el `width=device-width` de la
  página y renderiza con un viewport ancho (Chrome usa ~980px por defecto
  para "Desktop site"), y luego escala la página completa para que entre en
  la pantalla física → de ahí "Dashboard/Buscar siguen viéndose como versión
  **desktop reducida**" — es literalmente eso: la versión desktop, reducida.
- Con viewport ≥768px, **todas** las variantes `md:` de P1 quedan activas
  permanentemente → Álbum nunca usa `grid-cols-5`/`h-11`, Faltantes/
  Repetidas nunca usan `px-3 py-3 text-sm font-bold gap-2` → "Faltantes
  continúa mostrando ~20 badges casi en una sola línea" y "Repetidas
  mantiene el mismo patrón" quedan explicados exactamente.
- Todo el contenido (incluyendo `Layout.jsx`, que no tiene variantes `md:`
  para los íconos/texto del bottom nav) se renderiza a tamaño "desktop" y
  luego se reduce visualmente → "Bottom Navigation sigue siendo
  extremadamente pequeña" y "el usuario sigue necesitando zoom para leer".

Es decir: **P1 puede estar perfectamente implementado (y de hecho, según la
verificación de código de la sección 1, lo está) y aun así ser
completamente invisible en este dispositivo**, porque el punto de corte
`<768px` que activa las clases mobile de P1 **nunca se alcanza** si el
navegador está reportando un viewport de escritorio.

### Qué NO se puede determinar sin más información

- Si el `dist/` en el VPS ya incluye `ee0b5a7` o no (sigue siendo relevante,
  ver §2) — pero **no es la causa de que estas 5 capturas no muestren
  diferencia**, porque aunque lo incluyera, no se vería con este viewport.
- Si el modo "Desktop site" está activado a nivel de Chrome (toggle del
  menú ⋮), a nivel de una app/launcher que envuelve el navegador, o si el
  dispositivo tiene configurada una densidad de pantalla/zoom de sistema
  atípica. Cualquiera de estas causas produce el mismo síntoma visual.

---

## 0. Hallazgo principal (lote de capturas original — sigue vigente como contexto)

**No existe ninguna captura de Android posterior a la implementación de
P1.** Las 4 capturas disponibles en la carpeta de evidencia
(`1000666185.jpg`, `1000666235.jpg`, `1000666236.jpg`, `1000666237.jpg`) son
**las mismas 4 capturas** que ya se usaron como fuente única para
`MOBILE_UX_REDESIGN_MASTERPLAN.md`. No se agregó ningún archivo nuevo a la
carpeta.

Cronología verificada (`git log`, capturas tomadas según
`MOBILE_UX_REDESIGN_MASTERPLAN.md` §0):

| Hora | Evento |
|---|---|
| 10:34 | Captura `1000666185.jpg` (Álbum) |
| 11:34 | Commit `50c8083` "Fix mobile layout and code 00 display" |
| 11:40 | Captura `1000666235.jpg` (Dashboard) |
| 11:41 | Captura `1000666236.jpg` (Dashboard scroll) |
| 11:42 | Captura `1000666237.jpg` (Álbum scroll) |
| 12:30 | Commit `ee0b5a7` "Mobile P1 UX improvements" |

**Las 4 capturas fueron tomadas entre las 10:34 y las 11:42. El commit de
P1 (`ee0b5a7`) se creó a las 12:30 — casi una hora *después* de la última
captura.**

Conclusión directa: es **imposible** que estas 4 capturas muestren el
resultado de P1, porque en el momento en que se tomaron, el código de P1 ni
siquiera existía. "Tomar las capturas como fuente única de verdad" es
correcto como principio, pero la fuente de verdad disponible es **anterior**
al cambio que se quiere validar.

Esto no significa que P1 haya funcionado — significa que **todavía no hay
evidencia que permita afirmar ni negar eso**. El resto de este informe busca
la causa más probable de que, *cuando se tomen capturas nuevas*, el
resultado siga sin verse distinto — y por qué algunas de las observaciones
reportadas (Dashboard, Buscar, Bottom Nav) ya eran esperables incluso si P1
funcionara perfectamente.

---

## 1. Verificación: ¿el código de P1 está realmente en el repo?

Sí. Se releyeron los 3 archivos modificados y los cambios descritos en
`MOBILE_P1_IMPLEMENTATION_REPORT.md` están presentes tal cual:

| Archivo | Componente | Línea | Clase efectiva (mobile, <768px) |
|---|---|---|---|
| `frontend/src/pages/Album.jsx` | `CountryCard`, grilla de badges | L125 | `grid grid-cols-5 gap-2` (antes `grid-cols-8 gap-1`) |
| `frontend/src/pages/Album.jsx` | `CountryCard`, botón de badge | L132 | `flex h-11 items-center justify-center rounded-lg text-sm font-bold ...` (antes `h-8 text-xs font-semibold`) |
| `frontend/src/pages/Album.jsx` | resumen país | L105, L108 | `text-sm text-gray-500` / `text-sm` (antes `text-xs`) |
| `frontend/src/pages/Album.jsx` | `ProgressRing` % | L121 | `text-sm font-bold` (antes `text-xs`) |
| `frontend/src/pages/Missing.jsx` | badge de número | L50, L54 | `flex flex-wrap gap-2` / `flex items-center justify-center rounded-full ... px-3 py-3 text-sm font-bold` (antes `gap-1` / `px-2 py-1 text-xs font-semibold`) |
| `frontend/src/pages/Duplicates.jsx` | badge de número | L50, L54 | idéntico a Missing.jsx, con formato `N (xQ)` |

`git status` confirma que no hay cambios sin commitear: todo lo anterior ya
está en el commit `ee0b5a7`, pusheado a `main`.

**Esto descarta una hipótesis posible**: que el código se haya escrito pero
no se haya guardado/compilado/commiteado correctamente. El código P1 está
completo, correcto y en el repositorio remoto.

---

## 2. La causa más probable: gap de despliegue

`DEPLOY.md` describe el proceso de despliegue real de este proyecto:

- El frontend se sirve como **archivos estáticos** desde
  `/opt/stickercontrol-2026/frontend/dist/`, vía `nginx alias`
  (`location /stickercontrol/ { alias .../dist/; ... }`).
- Ese `dist/` se genera con `npm run build` **ejecutado manualmente en el
  VPS**, dentro de `/opt/stickercontrol-2026/frontend`.
- **No existe ningún paso de CI/CD, webhook, ni script de auto-deploy** en
  `DEPLOY.md`. El flujo documentado es: clonar/actualizar el repo en el VPS
  → `npm install` → `npm run build` → nginx sirve el `dist/` resultante
  directamente (sin copiarlo a otra carpeta, sin reiniciar nada).

Esto implica que:

- `git push` a GitHub (lo único que se hizo en esta sesión, commit
  `ee0b5a7`) **no afecta en absoluto** a lo que `skillgames.com.ar` sirve.
- El `dist/` que nginx sirve en este momento en el VPS es el resultado del
  **último `npm run build` ejecutado manualmente allí** — que, según la
  evidencia disponible, corresponde como mucho al commit `50c8083` (el fix
  de layout anterior, que según el masterplan "ya está aplicado" en las
  capturas), y **no incluye `ee0b5a7` (P1)**.

**Si se tomara una captura de Android contra producción en este momento, no
podría mostrar los cambios de P1 — sin importar si el código de P1 es
correcto o no — porque el `dist/` desplegado todavía no lo incluye.**

Esta es la causa raíz más probable de "P1 no produjo cambio visual": **P1
nunca llegó a producción**, no porque el código esté mal, sino porque
desplegar requiere un paso manual adicional en el VPS que no se ha
ejecutado (y que está fuera del control de este repositorio local).

---

## 3. Desajuste de alcance: 3 de las 6 observaciones eran esperables

Comparando las observaciones reportadas contra el alcance que el propio
usuario definió para P1 (`MOBILE_IMPLEMENTATION_BACKLOG_V2.md` + mensaje
"IMPLEMENTAR P1 MOBILE UX", restricciones explícitas: *"NO rediseñar
Dashboard todavía"*, *"NO rediseñar Bottom Navigation todavía"*, y Buscar
nunca apareció en el alcance de P1):

| Observación reportada | ¿Estaba en alcance de P1? | Estado esperado |
|---|---|---|
| "Dashboard sigue viéndose como desktop reducida" | **No** — explícitamente excluido | Sin cambios — correcto según spec |
| "Buscar sigue viéndose como desktop reducida" | **No** — nunca formó parte de P1/V2 | Sin cambios — correcto según spec |
| "Bottom Navigation sigue siendo extremadamente pequeña" | **No** — explícitamente excluido (reservado a P3) | Sin cambios — correcto según spec |
| "Faltantes continúa mostrando 20 badges en una sola línea" | **Sí** (P1-2) | Debería verse distinto — bloqueado por §2 (deploy) |
| "Repetidas mantiene el mismo patrón" | **Sí** (P1-3) | Debería verse distinto — bloqueado por §2 (deploy) |
| "Usuario sigue necesitando zoom" | Parcialmente (Álbum/Faltantes/Repetidas sí, Dashboard/Buscar/Nav no) | Mixto |

Es decir: **3 de las 6 quejas (Dashboard, Buscar, Bottom Nav) no son una
falla de P1 — son el comportamiento correcto de un cambio que
deliberadamente no tocó esas pantallas.** Las 2 quejas que sí corresponden
al alcance de P1 (Faltantes, Repetidas) son explicables completamente por el
gap de despliegue de §2, sin necesidad de asumir que el código esté mal.

---

## 4. Captura conceptual del layout actual

Basado en las únicas capturas disponibles (pre-P1, y — según §2 — muy
probablemente idénticas a lo que sigue sirviendo producción hoy), el layout
actual es:

```
┌─────────────────────────────────────┐
│ DASHBOARD                            │
│ ┌───────────────────────────────────┐│
│ │ [verde] Mi Álbum Mundial 2026      ││
│ │            ◯ 0.1%                  ││  ← ring pequeño, mucho
│ │         (anillo chico,             ││    relleno verde vacío
│ │          mucho fondo verde)        ││    alrededor (D2)
│ └───────────────────────────────────┘│
│ 🏳🏳🏳🏳🏳🏳... (banderas 24px,      │  ← tira angosta,
│ scroll horizontal sin pista) (D4)     │    sin indicio de scroll
│ ┌──────┬──────┬──────┐                │
│ │Pegadas│Falt. │Repet.│  (3 stats)    │
│ └──────┴──────┴──────┘                │
│ Accesos rápidos                       │
│ ┌─────────┬─────────┐                 │
│ │ Buscar  │ Álbum   │                 │  ← grilla 2 col,
│ ├─────────┼─────────┤                 │    íconos chicos,
│ │Faltantes│Repetidas│                 │    mucho espacio
│ ├─────────┴─────────┤                 │    muerto por celda (D3)
│ │ Usuarios cerca     │                 │
│ └────────────────────┘                 │
│                                        │
│         (espacio vacío,               │  ← ~50% del viewport
│          ~50% del alto                │    sin contenido (D1)
│          restante)                    │
│                                        │
├─────────────────────────────────────┤
│ [Inicio][Buscar][Álbum][Falt][Rep]... │  ← 7 items, grid-cols-7,
│  ico 28px  texto 10px                 │    cada uno ~50px de
└─────────────────────────────────────┘     ancho en pantalla 360px

┌─────────────────────────────────────┐
│ ÁLBUM                                 │
│ ┌───────────────────────────────────┐│
│ │ 🏳 Alemania      9/20 pegadas   ◯54%││ ← tarjeta país: bandera
│ │     0 falt · 0 repet              │ │   24x16, texto xs, ring
│ │ [1][2][3][4][5][6][7][8][9][10]   │ │   ~50px
│ │ [20]                               │ │  ← grilla 8/10 columnas,
│ │  (11-19 fuera de vista a este zoom)│ │    badges ~28px alto,
│ └───────────────────────────────────┘│    fila de 8-10 + sobrante
│ ┌───────────────────────────────────┐│
│ │ 🏳 Curaçao  ... (mismo patrón)     │ │  ← se repite x49 países,
│ └───────────────────────────────────┘│    todas expandidas,
│            ⋮ (x49 tarjetas)           │    scroll vertical enorme
└─────────────────────────────────────┘

FALTANTES / REPETIDAS (mismo patrón, inferido):
┌─────────────────────────────────────┐
│ 🏳 Alemania (DEU)                     │
│ (1)(2)(3)(4)(5)(6)(7)(8)(9)(10)(11)   │  ← flex-wrap, badges
│ (12)(13)(14)(15)(16)(17)(18)(19)(20)  │    px-2 py-1 text-xs,
│  (todos en una sola "pared" de chips  │    ~24px alto, se acumulan
│   rojos/amarillos muy juntos)         │    en filas largas sin
└─────────────────────────────────────┘    estructura de grilla
```

Cada una de las "P1 changes" (badges más grandes en Álbum/Faltantes/
Repetidas con `md:` para no afectar desktop) modifica exactamente las
secciones marcadas arriba con grillas/chips — pero si el `dist/` desplegado
es anterior a `ee0b5a7`, este diagrama sigue siendo 100% representativo de
lo que un usuario ve hoy en `skillgames.com.ar/stickercontrol/`,
**incluyendo** Álbum/Faltantes/Repetidas.

---

## 5. Propuesta MOBILE P2 REAL (rediseño, no ajuste cosmético)

Importante: esta sección es una **propuesta para evaluación**, no una
implementación. Asume que, una vez resuelto el gap de despliegue (§2) y
confirmado con capturas reales post-deploy, **todavía** se considere
necesario un rediseño estructural (no solo de tamaños).

### 5.1 Álbum — de "tabla de escritorio" a "lista con detalle expandible"

Problema estructural (no de tamaño): **49 tarjetas de país, cada una con su
grilla completa de 20 badges, todas renderizadas y expandidas
simultáneamente**. Esto es un patrón de tabla de escritorio ("todo visible,
scroll con rueda de mouse"), no un patrón mobile.

Rediseño propuesto:

- **Tarjeta de país con dos estados**: colapsada (default) muestra bandera,
  nombre, barra de progreso lineal (no `ProgressRing`) y contadores
  faltantes/repetidas — sin grilla de badges. Expandida (al tocar la
  tarjeta) muestra la grilla de badges.
- Con esto, solo 1-2 tarjetas están expandidas a la vez → la grilla de
  badges puede usar **menos columnas y badges más grandes** (ej. 4 columnas
  en vez de 5/10) sin que el scroll total de la página se vuelva
  inmanejable.
- Sustituir `ProgressRing` (56px, difícil de leer a esa escala x49) por una
  barra de progreso horizontal de ancho completo dentro de la tarjeta
  colapsada — más legible y más compacta verticalmente.
- Mantener el orden por grupo (A-L) como anclas de navegación, pero
  considerar un selector/chip horizontal sticky para saltar entre grupos sin
  scrollear las 49 tarjetas.

### 5.2 Faltantes / Repetidas — de "pared de chips" a "grilla numerada"

Problema estructural: los números faltantes/repetidos se renderizan como
una lista `flex flex-wrap` de chips de ancho variable. Con 20 elementos por
país, esto produce líneas de longitud impredecible y, en pantallas angostas,
una "pared" densa de chips pequeños pegados unos a otros.

Rediseño propuesto:

- Reemplazar el contenedor `flex flex-wrap` por una **grilla de ancho fijo**
  (ej. `grid grid-cols-5` en mobile), igual que la grilla de Álbum — así
  cada número ocupa una celda de tamaño predecible y alineado, en vez de
  fluir según el ancho del texto.
- Para países con muchos faltantes (ej. 20/20), considerar **colapsar por
  país** igual que en Álbum (resumen "20 faltantes" + botón "ver todos"),
  consistente con el patrón de 5.1 y reduciendo el scroll total de la
  página cuando hay muchos países con faltantes completos.
- El botón "Copiar para WhatsApp" ya es full-width y prominente — mantenerlo
  como está, es un buen patrón mobile.

### 5.3 Bottom Navigation — evaluación de 7 items en `grid-cols-7`

Estado actual: 7 items (`Inicio, Buscar, Álbum, Faltantes, Repetidas,
Cambios, Cerca`) en `grid-cols-7`, cada uno con ícono `h-7 w-7` (28px) y
texto `text-[10px]`. En un viewport de ~360px, cada item ocupa ~51px de
ancho total — el ícono+texto+padding deben caber en ese ancho, lo que
explica que se vea "extremadamente pequeña".

Rediseño propuesto (a validar con datos de uso real, no solo estética):

- Reducir a **4-5 items primarios** visibles directamente (candidatos por
  frecuencia de uso: Inicio, Álbum, Faltantes, Repetidas) + un quinto slot
  "Más" que despliega Buscar/Cambios/Cerca en un menú o bottom-sheet. Esto
  permite que cada item primario ocupe ~72-90px de ancho, suficiente para
  ícono `h-8 w-8` + texto `text-xs` sin saturar.
- Alternativa sin ocultar nada: mantener 7 items pero **eliminar las
  etiquetas de texto** y dejar solo iconos `h-8 w-8` más grandes con
  `aria-label` para accesibilidad — reduce la necesidad de texto a 10px pero
  conserva las 7 rutas visibles.
- Cualquiera de las dos opciones requiere **datos de uso** (qué rutas se
  visitan más) para decidir cuáles 4-5 son "primarias" — no se debe decidir
  solo por intuición de diseño, tal como se indicó en la restricción P3
  original.

---

## 6. Próximos pasos recomendados (no implementados)

**Orden de prioridad revisado tras `imagenes/v2`:**

1. **Verificar y desactivar "Solicitar sitio de escritorio" / resetear el
   zoom del navegador en el dispositivo Android usado para las capturas.**
   En Chrome: menú ⋮ → confirmar que "Sitio de escritorio" / "Desktop site"
   **no** esté marcado para `skillgames.com.ar`, y que el nivel de zoom de
   la página esté en 100%. Esto es un ajuste **del dispositivo/navegador**,
   no del código — no requiere ningún cambio en el repo.
2. **Recién con el navegador en modo móvil real**, repetir las 5 capturas
   (Dashboard, Buscar, Álbum, Faltantes, Repetidas) y comparar:
   - Álbum: ¿la grilla pasa de 10 a 5 columnas, con badges más altos
     (`h-11`)?
   - Faltantes/Repetidas: ¿los badges pasan a `px-3 py-3 text-sm font-bold`
     con `gap-2` (menos elementos por fila, más grandes)?
   - Si **sí** cambian → P1 funciona correctamente y ya está en
     producción; las observaciones originales (Dashboard, Buscar, Bottom
     Nav) quedan como pendientes de P2/P3 (fuera del alcance de P1, según
     §3).
   - Si **no** cambian incluso en modo móvil real → entonces sí aplica la
     hipótesis de §2 (gap de deploy): confirmar si
     `/opt/stickercontrol-2026/frontend/dist/` en el VPS corresponde al
     commit `ee0b5a7` (buscar `grid-cols-5`, `h-11` en el CSS servido, o
     comparar el hash `index-B4z0kzyn.css` / `index-6odBvM3O.js`) y, si no,
     ejecutar el deploy de `DEPLOY.md` §2.
3. Solo después de los pasos 1-2 tiene sentido evaluar si se necesita
   "MOBILE P2 REAL" (§5) — hoy no hay evidencia válida de que el rediseño
   estructural sea necesario, porque ninguna captura disponible refleja
   todavía el comportamiento móvil real de P1.
