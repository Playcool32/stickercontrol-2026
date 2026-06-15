# Causa raíz — columna angosta en Android (Fase 2)

**Solo diagnóstico — sin implementación.** Foco exclusivo: contenedores,
`max-width`/`width`, `margin auto`, `padding`, wrappers de layout, en
`App.jsx` (shell), `Layout.jsx`, `Dashboard.jsx`, `Album.jsx`, `Search.jsx`.
Quedan descartadas (por evidencia de producción) las hipótesis de Vite
`base`, `BrowserRouter basename`, meta viewport, HTTPS, nginx y API.

## Causa raíz identificada

**Archivo**: `frontend/src/components/Layout.jsx`
**Líneas**: 26 y 31
**Selector**: `.max-w-2xl` (Tailwind → `max-width: 42rem` = **672px**)
combinado con `.mx-auto` (`margin-left: auto; margin-right: auto`)

```jsx
// línea 26
<main className="mx-auto flex-1 w-full max-w-2xl p-4 pb-24">
  <Outlet />
</main>

// línea 31
<div className="mx-auto grid max-w-2xl grid-cols-7">
  {/* 7 items de navegación */}
</div>
```

### Por qué es la causa raíz

`Layout.jsx` es el **único wrapper compartido** por todas las páginas
(`Dashboard`, `Search`, `Album`, `Missing`, `Duplicates`, `Nearby`, `Trades`)
vía `<Route element={<Layout />}>` en `App.jsx`. Todo el contenido de cada
página entra como `<Outlet />` **dentro** de este `<main>`. Por lo tanto,
cualquier restricción de ancho puesta acá afecta a *toda la app por igual* —
coincide exactamente con el alcance reportado (Dashboard, Álbum, Buscar, app
shell, todas angostas por igual).

`max-w-2xl` (672px) + `mx-auto` es el **patrón clásico de "contenedor
centrado de escritorio"** (`.container { max-width: 672px; margin: 0 auto }`),
heredado de layouts desktop/blog, no de un layout mobile-first puro. Es
inofensivo mientras el viewport sea **más angosto que 672px** (el contenedor
ocupa el 100% gracias a `w-full`, el `max-width` nunca llega a aplicarse). El
problema aparece cuando el **ancho efectivo del viewport CSS en el celular
real (`window.innerWidth`) es mayor a 672px**:

- En esos casos, `<main>` y el `<nav>` interno **dejan de ocupar el 100% del
  ancho** y quedan fijados a exactamente `672px`, centrados con `mx-auto`.
- El resto de la pantalla (a ambos lados del contenedor de 672px) queda con
  el fondo `bg-gray-50` del `<div>` raíz (`Layout.jsx` línea 25:
  `className="flex min-h-screen flex-col bg-gray-50"`), sin contenido.

### Cuándo ocurre esto en Android real

`window.innerWidth` puede superar 672px CSS px en escenarios habituales en
celulares Android modernos, sin que el usuario haga nada raro:

- **Pantallas grandes (6.5"-6.9") con la opción "Tamaño de pantalla" /
  "Display size" de Android reducida** (Ajustes → Pantalla → Tamaño de
  fuente y pantalla → más chico que el valor por defecto). Esta opción es
  muy usada porque "se ve más contenido" — y técnicamente aumenta
  `window.innerWidth` en CSS px. Es muy común que termine entre ~480px y
  ~760px según el modelo.
- **Orientación horizontal (landscape)**: un teléfono de 412×915 (Pixel/
  Samsung típico) pasa a `915×412` en horizontal → `915px > 672px`.
- **Modo "Pantalla dividida" / multi-ventana** en tablets/phablets Android.

En cualquiera de estos casos, **el viewport meta tag funciona correctamente**
(`width=device-width` ya refleja ese ancho mayor), **el build, el HTTPS, el
nginx y la API funcionan** (por eso esas hipótesis quedan descartadas) — el
problema es puramente que `max-w-2xl` le pone un techo de 672px a la UI
*independientemente* de cuánto espacio real tenga el dispositivo.

## "Screenshot mental" de cómo se vería

```
Pantalla del celular (ej. 760px de ancho efectivo, landscape o display-size chico)

┌──────────────────────────────────────────────────────────┐
│ gris │                                                │ gris │
│ (bg- │   ┌──────────────────────────────────────┐    │ (bg- │
│ gray │   │  StickerControl 2026                  │    │ gray │
│  -50)│   │  [Dashboard / Álbum / Buscar...]      │    │  -50)│
│  ~44 │   │  contenido normal, responsive,        │    │  ~44 │
│  px  │   │  pero acotado a 672px de ancho        │    │  px  │
│      │   └──────────────────────────────────────┘    │      │
│      │   ┌──────────────────────────────────────┐    │      │
│ gris │   │ [Inicio][Buscar][Álbum]...7 íconos    │    │ gris │
│      │   └──────────────────────────────────────┘    │      │
└──────────────────────────────────────────────────────────┘
        ↑ contenido real: 672px, centrado            ↑
```

Visualmente esto se percibe exactamente como lo describe el reporte:

- **"el layout se ve demasiado angosto"** → la columna de 672px en una
  pantalla de >672px deja franjas grises vacías a los costados.
- **"el contenido parece escalado"** → una franja central angosta con todo
  el contenido "de teléfono" (nav inferior de 7 íconos, tarjetas, grilla)
  rodeada de espacio vacío da la sensación de una vista de escritorio
  reducida/"zoomeada hacia adentro", no de una app mobile a pantalla
  completa.
- **"no se aprovecha el ancho disponible"** → literal: ~672px de 760px+
  disponibles, el resto es `bg-gray-50` sin uso.
- **"experiencia mobile inferior a desktop"** → en PC, 672px centrados
  dentro de una ventana de 1920px es un patrón *esperado* y se ve bien
  (columna de lectura). En un celular, esa misma columna ya no se siente
  "centrada con margen elegante" sino "rota / no ocupa la pantalla".

## Selectores relacionados (mismo patrón, menor alcance)

| Archivo | Línea | Selector | Alcance |
|---|---|---|---|
| `frontend/src/components/Layout.jsx` | 26 | `.max-w-2xl.mx-auto.w-full` en `<main>` | **Todas las páginas** (root cause principal) |
| `frontend/src/components/Layout.jsx` | 31 | `.max-w-2xl.mx-auto` en el `<div>` del `<nav>` | Nav inferior (7 íconos) — mismo ancho de 672px, mismo efecto de "franjas" debajo |
| `frontend/src/components/StickerDetailModal.jsx` | 26 | `.max-w-lg.w-full` (512px) en el panel del modal | Solo modal de detalle de figurita (Álbum) — mismo patrón pero con techo más bajo (512px), mismo riesgo en pantallas >512px |

`Dashboard.jsx`, `Album.jsx` y `Search.jsx` **no agregan ningún `max-width`
ni `width` propio** — todo su contenido es `w-full`/`flex`/`grid` de ancho
relativo (100% de su contenedor). Por eso la causa raíz no está en esas
páginas individualmente, sino en el wrapper común (`Layout.jsx`) que las
contiene a todas.

## Confirmación rápida (sin implementar)

En el celular real, abrir la consola remota (`chrome://inspect` desde PC con
el celular por USB, o un bookmarklet) y ejecutar:

```js
[window.innerWidth, document.querySelector('main').getBoundingClientRect().width]
```

- Si `window.innerWidth > 672` y el segundo valor es exactamente `672` →
  **causa raíz confirmada al 100%**.
- Si ambos valores coinciden (≈ iguales) → el `max-w-2xl` no se está
  aplicando y habría que revisar otra hipótesis (poco probable dado el
  análisis de código).

## Resumen

- **Causa raíz**: `max-w-2xl` (672px) + `mx-auto` en `frontend/src/components/Layout.jsx:26` (y su réplica en la línea 31 para el nav inferior) — un patrón de "contenedor centrado de escritorio" que limita el ancho de **toda la app** (Dashboard, Álbum, Buscar, nav) a 672px sin importar cuánto ancho real tenga el dispositivo.
- **Por qué no se ve en PC**: 672px centrados en una ventana de escritorio (1280px+) es un patrón visualmente normal/esperado (columna de lectura con márgenes).
- **Por qué se ve mal en Android real**: varios celulares modernos reportan `window.innerWidth` por encima de 672px (pantallas grandes con "tamaño de pantalla" reducido, u orientación horizontal), y ahí el `max-width: 672px` deja de ser "ocupa toda la pantalla" y pasa a ser una restricción real, generando la columna angosta centrada con franjas vacías a los costados.
- **No implementado**: ningún archivo fue modificado en esta sesión. Esta es solo la identificación de causa raíz solicitada para la Fase 2.
