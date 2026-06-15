# Auditoría mobile — StickerControl 2026 (post-deploy SkillGames)

**Solo auditoría — sin implementación.** Objetivo: diagnosticar por qué en
celular Android real el layout "se ve angosto", "el contenido parece
escalado" y "no se aprovecha el ancho disponible", mientras en PC funciona
bien.

## 0. Limitación importante

Las capturas de pantalla mencionadas en el pedido **no llegaron a este
entorno** (esta sesión no tiene acceso a imágenes adjuntas). Esta auditoría
se basa en:

- Revisión completa del código frontend (`vite.config.js`, `index.html`,
  `index.css`, `main.jsx`, `Layout.jsx`, todas las páginas y componentes).
- Revisión de `dist/index.html` (build ya generado).
- Revisión de `DEPLOY.md` / `DEPLOY_SKILLGAMES_REPORT.md` (config real de
  nginx documentada).
- Revisión de `LOCAL_UX_AUDIT.md` (auditoría previa, Fase 0.6.5).

No se pudo abrir la URL productiva (`https://skillgames.com.ar/stickercontrol/`)
desde este entorno ni inspeccionar el HTML/CSS realmente servido por el VPS.
Por eso esta auditoría entrega **hipótesis de causa raíz ordenadas por
probabilidad**, cada una con su forma de confirmarla, en vez de un único
diagnóstico cerrado. Antes de implementar cualquier fix conviene correr el
"Protocolo de diagnóstico rápido" de la sección 5.

## 1. Lo que se verificó y está OK (vite.config / CSS global)

Esto responde directamente al pedido de verificar si quedó algo mal
configurado del deploy:

- **`frontend/vite.config.js`**: `base: mode === "production" ? "/stickercontrol/" : "/"`
  — correcto, coincide con lo documentado en `DEPLOY_SKILLGAMES_REPORT.md`.
- **`frontend/src/main.jsx`**: `basename = import.meta.env.BASE_URL.replace(/\/$/, "")`
  — correcto, `BrowserRouter` recibe `/stickercontrol` en producción.
- **`frontend/dist/index.html`** (build ya generado): referencia
  `/stickercontrol/assets/index-*.js` y `/stickercontrol/assets/index-*.css`,
  e incluye:
  ```html
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  ```
  Esto está presente **tanto en `frontend/index.html` (fuente) como en
  `frontend/dist/index.html` (build)** — el viewport tag no se perdió en el
  build.
- **`frontend/src/index.css`**: solo define `html, body, #root { height: 100% }`,
  `body { margin: 0; font-family: ...; background-color: #f3f4f6 }`. No hay
  `width` fijo, `min-width`, `overflow`, `transform: scale()` ni `zoom` en
  ningún CSS global.
- **`frontend/tailwind.config.js`**: solo agrega 4 colores custom
  (`faltante`/`disponible`/`pegada`/`repetida`). No hay breakpoints
  personalizados que puedan estar empujando el diseño a un modo "desktop"
  por error.

**Conclusión de este punto**: no se encontró ninguna configuración de Vite,
Tailwind o CSS global que explique por sí sola "contenido escalado /
desaprovecha el ancho". El build de producción es consistente con el código
fuente.

## 2. Revisión de cada página (búsqueda de anchos fijos / overflow horizontal)

Se revisaron `Layout.jsx`, `Dashboard.jsx`, `Search.jsx`, `Album.jsx`,
`Missing.jsx`, `Duplicates.jsx`, `Nearby.jsx`, `Trades.jsx`,
`StickerCard.jsx`, `StickerDetailModal.jsx`, `ProgressRing.jsx`, `icons.jsx`.

- Contenedor raíz: `Layout.jsx` → `<main className="mx-auto flex-1 w-full max-w-2xl p-4 pb-24">`.
  `max-w-2xl` (672px) con `w-full` → en pantallas <672px ocupa el 100% del
  ancho. Esto es correcto para mobile-first.
- No se encontró ningún `width:` fijo en px, `min-width`, `100vw`,
  `<table>`, `<pre>` ni `<textarea>` que pudiera forzar un ancho de documento
  mayor al del viewport (búsqueda exhaustiva por estos patrones, sin
  resultados salvo `ProgressRing` que usa `style={{width:size,height:size}}`
  con tamaños 56px/168px — no causan overflow).
- Único `overflow-x-auto` intencional: `Dashboard.jsx:78` (tira horizontal de
  banderas), correctamente contenido con `flex-shrink-0` en sus hijos.
- **`frontend/src/components/Layout.jsx` (nav inferior)**: `grid-cols-7` con
  etiquetas `text-[10px]` ("Inicio", "Buscar", "Álbum", "Faltantes",
  "Repetidas", "Cambios", "Cerca"). Ya señalado como riesgo MEDIO en
  `LOCAL_UX_AUDIT.md` §7-8 ("nav inferior con 7 ítems en pantallas
  angostas ~320px"), **nunca verificado en dispositivo real**. Esto puede
  hacer que el nav se vea apretado, pero no explica que *todo el contenido*
  se vea escalado/angosto — es un hallazgo aparte, no la causa raíz buscada.
- **`Album.jsx:125`** (`grid grid-cols-8 gap-1 sm:grid-cols-10`): las celdas
  usan `flex h-8` sin ancho fijo (el ancho lo define el grid en `fr`), por lo
  que no deberían desbordar horizontalmente en ningún ancho de pantalla.

**Conclusión de este punto**: el código de las páginas es responsive y no
tiene elementos que, por sí mismos, fuercen un `document.body.scrollWidth`
mayor que el viewport. Esto reduce la probabilidad de que la causa sea "un
elemento ancho que hace zoom-out a toda la página", pero no la descarta del
todo sin verlo en el dispositivo (hay banderas `<img>` cuyo tamaño intrínseco
no se conoce sin verlas).

## 3. Hipótesis de causa raíz (ordenadas por probabilidad)

### H1 — El VPS está sirviendo un build (`dist/`) desactualizado (ALTA probabilidad)

- **Por qué es probable**: el deploy se hizo clonando el repo y siguiendo
  `DEPLOY.md`, pero hubo **varios commits/cambios posteriores al checkpoint**
  (`GROUP_ORDER_IMPLEMENTATION_REPORT.md`, `FWC_CODE_MIGRATION_REPORT.md`,
  landing del Dashboard en 0.6.2). Si `npm run build` se corrió **una sola
  vez, antes** de algunos de estos cambios, o si se corrió `npm run dev` en
  vez de `npm run build` en algún momento y luego no se regeneró `dist/`,
  el VPS podría estar sirviendo HTML/CSS/JS de una versión distinta a la que
  se ve en local (PC) si en PC se está probando con `npm run dev` (servidor
  de desarrollo, siempre "fresco") en vez de la build estática.
- **Cómo se manifestaría como "angosto/escalado"**: si el build servido es
  de **antes** de que `index.html` tuviera el meta viewport correcto, o de
  una versión del CSS de Tailwind sin las clases responsive actuales
  (purga de Tailwind distinta), el resultado visual sería exactamente
  "se ve como una versión de escritorio comprimida".
- **Archivos responsables**: `frontend/dist/` en el VPS
  (`/opt/stickercontrol-2026/frontend/dist/` según `DEPLOY.md`, aunque
  `PROJECT_STATE.md`/el resumen del usuario menciona
  `/var/www/skillgames/stickercontrol-2026` — **discrepancia de ruta a
  confirmar**, ver H4).
- **Cómo confirmar**: en el VPS, `curl -s https://skillgames.com.ar/stickercontrol/ | head -20`
  y comparar contra el `frontend/dist/index.html` local (mismo hash de
  archivos `assets/index-*.js`/`.css`). Si difiere, hay que re-buildear y
  redesplegar.

### H2 — Autosizing/"font boosting" de Android Chrome en columnas angostas (MEDIA-ALTA probabilidad)

- **Qué es**: Android Chrome (y WebViews basados en Chromium) aplican un
  algoritmo de *text autosizing* que **agranda automáticamente el texto**
  cuando detecta un bloque de contenido más angosto que el viewport, para
  compensar la lectura en "modo desktop comprimido". Esto se desactiva con
  `-webkit-text-size-adjust: 100%`, que **no está presente** en
  `frontend/src/index.css`.
- **Por qué calza con el síntoma**: este algoritmo no se replica en Chrome
  DevTools (emulación de PC) ni siempre en `npm run dev` visto desde PC —
  por eso "en PC se ve bien" y solo en celular real se nota. El efecto
  típico es texto/elementos con tamaños inconsistentes y una sensación de
  "la app no usa el ancho como debería", aunque el layout subyacente sea
  responsive.
- **Archivo responsable**: `frontend/src/index.css` (falta la regla).
- **Cómo confirmar**: en el celular, activar "Solicitar sitio de escritorio"
  en Chrome — si el layout se ve "más parecido a PC" (aunque más chico),
  apunta a autosizing. También se puede confirmar inspeccionando
  remotamente vía `chrome://inspect` desde una PC conectada por USB con
  depuración habilitada.
- **Fix propuesto** (si se confirma): agregar a `index.css`:
  ```css
  html {
    -webkit-text-size-adjust: 100%;
    text-size-adjust: 100%;
  }
  ```
  **Riesgo: muy bajo** (una línea CSS estándar, ampliamente usada, no
  afecta PC). **Esfuerzo: minutos.**

### H3 — Overflow horizontal causado por un elemento no visible desde el código (banderas/imagenes) (MEDIA probabilidad)

- **Qué es**: algunas imágenes de banderas (`frontend/public/flags/*.png`)
  podrían tener un ancho intrínseco grande sin que el `<img>` lo limite
  *si* el navegador tarda en aplicar el CSS, o si alguna bandera tiene
  proporciones inusuales. Todos los `<img>` de banderas en el código tienen
  clases de tamaño fijo (`h-10 w-14`, `h-8 w-12`) + `object-cover`, lo cual
  debería prevenir esto, pero no se pudo verificar visualmente.
- **Por qué calza parcialmente**: un solo elemento que desborde
  horizontalmente el `<body>` puede hacer que Android renderice la página
  inicial "zoomeada" para mostrar el ancho total del documento, lo cual se
  percibe como "todo escalado y con espacio sin usar a los costados" — calza
  bien con la descripción del usuario.
- **Archivos responsables**: `frontend/src/index.css` (falta regla
  defensiva), potencialmente `frontend/public/flags/*.png` (assets, no
  código).
- **Fix propuesto** (defensivo, independiente de encontrar el elemento
  exacto): agregar a `index.css`:
  ```css
  html, body {
    overflow-x: hidden;
  }
  ```
  **Riesgo: bajo-medio**. Es un parche defensivo: previene el síntoma visual
  (zoom-out/scroll horizontal) pero no corrige la causa si existiera un
  elemento desbordando — por eso se recomienda combinarlo con inspección
  real en el dispositivo antes de depender solo de esto. **Esfuerzo:
  minutos** para aplicar, pero requiere confirmar en celular real que
  resuelve el síntoma.

### H4 — Configuración de nginx en el VPS no coincide exactamente con `DEPLOY.md` (MEDIA probabilidad, no verificable desde acá)

- **Qué se observó**: `DEPLOY.md` documenta el bloque nginx para
  `www.skillgames.com.ar` con `alias /opt/stickercontrol-2026/frontend/dist/;`,
  pero el resumen de deploy real del usuario indica el repo clonado en
  `/var/www/skillgames/stickercontrol-2026` y el dominio
  `skillgames.com.ar` (sin `www`). Como "Nginx configurado manualmente" (no
  siguiendo el bloque al pie de la letra), es posible que:
  - el `alias`/`root` apunte a una ruta de `dist/` distinta a la que se
    regenera con `npm run build` más reciente (sirviendo una copia vieja).
  - falten cabeceras de `Content-Type` correctas para `.css`/`.js` si se usó
    `root` en vez de `alias` con una estructura de carpetas distinta
    (aunque esto rompería la app también en PC, así que es menos probable
    dado que "PC funciona bien").
- **Archivos responsables**: configuración de nginx en el VPS (no versionada
  en este repo, "configurado manualmente").
- **Cómo confirmar**: revisar el bloque `server {}` real en el VPS
  (`/etc/nginx/sites-enabled/...`) y verificar que el `alias`/`root` apunte
  exactamente al `dist/` que se regenera, y que la fecha de modificación de
  `dist/index.html` en el VPS sea posterior al último `npm run build`.

### H5 — El "PC funciona bien" se probó en `npm run dev`, no contra el build de producción (BAJA-MEDIA probabilidad)

- Si las verificaciones de "Home/Buscar/Álbum funciona" en PC se hicieron
  contra `http://localhost:5173` (dev, `base: "/"`) y no contra
  `https://skillgames.com.ar/stickercontrol/` (build de producción,
  `base: "/stickercontrol/"`), una diferencia entre ambos modos (por ejemplo,
  si en algún momento se modificó algo y no se corrió `npm run build` de
  nuevo) no se habría detectado en PC. Esto refuerza H1: la comparación
  "PC bien / celular mal" puede no estar comparando lo mismo.
- **Cómo confirmar**: abrir `https://skillgames.com.ar/stickercontrol/`
  (la URL productiva) desde el navegador de PC y reducir la ventana a ancho
  mobile (~375px) con las DevTools — si ahí también se ve "angosto/escalado",
  el problema **no es específico de Android** sino del build/deploy (apunta
  a H1/H4). Si en PC con ancho mobile se ve bien pero en el celular real mal,
  apunta a H2 (autosizing, exclusivo de motores mobile reales).

## 4. Hallazgos adicionales (no son la causa raíz, pero conviene registrarlos)

1. **Nav inferior de 7 ítems (`Layout.jsx`)**: con `text-[10px]` y etiquetas
   como "Faltantes"/"Repetidas"/"Intercambios", en pantallas de ~320-360px
   de ancho cada celda mide ~46-51px. Riesgo de que el texto se corte o
   pase a dos líneas, ya señalado en `LOCAL_UX_AUDIT.md` y nunca verificado
   en dispositivo real. **No causa el síntoma de "todo escalado"**, pero es
   un punto a revisar en la misma sesión de pruebas con el celular.
2. **`ProgressRing` de 168px en `Dashboard.jsx`**: en una pantalla de 320px
   con `p-6` (padding del contenedor, 24px por lado) deja 272px de ancho
   disponible — el círculo de 168px entra con margen, no debería desbordar,
   pero es el elemento de mayor tamaño fijo en la pantalla principal y vale
   la pena confirmarlo visualmente.

## 5. Protocolo de diagnóstico rápido (antes de implementar nada)

Para no aplicar fixes a ciegas, se recomienda este orden (cada paso descarta
o confirma hipótesis):

1. **Desde PC**, abrir la URL productiva real
   (`https://skillgames.com.ar/stickercontrol/`, no `localhost`) y angostar
   la ventana a ~375px con DevTools.
   - Si se ve mal → **H1/H4** (problema de build/deploy, no de Android).
   - Si se ve bien → seguir al paso 2.
2. **Desde el celular**, en la misma URL, activar "Solicitar sitio de
   escritorio" en Chrome.
   - Si mejora notablemente → **H2** (text autosizing).
3. **Desde el celular**, ver "código fuente" de la página (o usar
   `chrome://inspect` desde una PC con el celular conectado por USB) y
   confirmar que el `<head>` tiene exactamente
   `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
   y que los `<link>`/`<script>` apuntan a `/stickercontrol/assets/...` con
   los mismos hashes que `frontend/dist/index.html` local.
   - Si los hashes difieren → **H1** confirmado (dist desactualizado).
4. **En el VPS**, comparar `ls -la` y hash (`md5sum`) de
   `frontend/dist/index.html` y `dist/assets/*` contra lo que nginx está
   sirviendo (`curl`), y verificar la ruta real en la config de nginx.
   - Confirma/descarta **H4**.

## 6. Resumen de propuestas de corrección (NO aplicadas)

| Hipótesis | Cambio propuesto | Archivo | Riesgo | Esfuerzo |
|---|---|---|---|---|
| H1 (dist desactualizado) | Re-ejecutar `npm run build` en el VPS y confirmar que nginx sirve ese `dist/` | VPS (deploy, sin cambio de código) | Bajo (operación estándar ya documentada en `DEPLOY.md`) | 15-30 min |
| H2 (font boosting Android) | Agregar `-webkit-text-size-adjust: 100%; text-size-adjust: 100%;` a `html` en `index.css` | `frontend/src/index.css` | Muy bajo | 5 min + rebuild |
| H3 (overflow horizontal defensivo) | Agregar `overflow-x: hidden` a `html, body` en `index.css` | `frontend/src/index.css` | Bajo-medio (parche defensivo, no corrige causa si existe) | 5 min + rebuild |
| H4 (nginx desalineado) | Alinear `alias`/`root` de nginx con la ruta real de `dist/` del clon (`/var/www/skillgames/stickercontrol-2026/frontend/dist/`) | VPS (nginx config, sin cambio de código) | Medio (tocar nginx en producción; requiere `nginx -t` + reload) | 15-30 min |
| Hallazgo nav (no causa raíz) | Revisar `grid-cols-7` / `text-[10px]` en `Layout.jsx` tras resolver lo anterior, ajustar si se confirma corte de texto | `frontend/src/components/Layout.jsx` | Bajo | 30-60 min |

**Estimación total de la Fase 1 (diagnóstico)**: ya completada (esta
auditoría). **Estimación de la Fase 2 (fix, una vez identificada la
hipótesis correcta con el protocolo de la sección 5)**: entre 15 minutos
(si es H1/H2, fixes triviales) y ~1 hora (si requiere ajustar nginx +
`index.css` + nav inferior + rebuild/redeploy completo).

## 7. Estado real del proyecto (resumen)

- Código fuente (`frontend/`) está correcto respecto a Vite `base`,
  `BrowserRouter` `basename`, `BASE_URL` del cliente API y CSS global — no
  hay regresiones introducidas por el deploy a nivel de configuración.
- El build (`frontend/dist/`) generado en este repo es consistente con el
  código fuente actual (viewport meta presente, rutas `/stickercontrol/...`
  correctas).
- El problema reportado en celular es **real y no está explicado por el
  código fuente actual** tal como está en este repo — la causa más probable
  está en **qué build está realmente desplegado en el VPS** (H1/H4) o en un
  comportamiento específico de Android (text autosizing, H2) que no
  requiere rediseñar nada, solo una línea de CSS.

## 8. Próximos pasos recomendados

1. Ejecutar el protocolo de diagnóstico de la sección 5 (no requiere tocar
   código, solo navegar/inspeccionar).
2. Según el resultado, aplicar **una** de las filas de la tabla de la
   sección 6 (probablemente H1 + H2 combinadas son las más probables y más
   baratas de aplicar).
3. Re-verificar en el celular real después del fix.
4. Aprovechar la misma sesión de prueba en celular para revisar el hallazgo
   del nav inferior (sección 4.1), ya señalado desde `LOCAL_UX_AUDIT.md` y
   pendiente desde Fase 0.6.5.

**No se modificó código, configuración ni base de datos en esta sesión.**
Solo se generó este archivo `MOBILE_UX_AUDIT.md`.
