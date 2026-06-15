# Responsive Structure Fix Report — StickerControl 2026

Reestructuración responsive **sin rediseño**: mismo contenido, colores,
iconos, textos y lógica. Solo se reorganiza la disposición de los elementos
existentes para que mobile y desktop tengan estructuras propias.

Patrón aplicado en todos los cambios: **clases sin prefijo = estructura
mobile reestructurada**, **`md:` = reproduce la estructura/tamaño desktop
actual**, igual criterio que `MOBILE_P1_IMPLEMENTATION_REPORT.md`.

No se modificó: backend, API, base de datos, lógica de negocio, rutas,
estado de React, paleta de colores, iconos, `ProgressRing`,
`StickerDetailModal`, `StickerCard`.

---

## 1. Archivos modificados

- `frontend/src/components/Layout.jsx` — navegación inferior
- `frontend/src/pages/Dashboard.jsx` — sección "Accesos rápidos"
- `frontend/src/pages/Album.jsx` — cabecera de `CountryCard`
- `frontend/src/pages/Missing.jsx` — contenedor de badges de números
- `frontend/src/pages/Duplicates.jsx` — contenedor de badges de números

---

## 2. Cambios por pantalla

### 2.1 Navegación inferior (`Layout.jsx`)

Se mantienen las **7 secciones actuales** (Inicio, Buscar, Álbum, Faltantes,
Repetidas, Cambios, Cerca) — ninguna se oculta.

```diff
-      <main className="w-full flex-1 p-4 pb-24 md:mx-auto md:max-w-2xl">
+      <main className="w-full flex-1 p-4 pb-28 md:mx-auto md:max-w-2xl md:pb-24">
```

```diff
-                  `flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-semibold leading-tight transition-colors ${
+                  `flex flex-col items-center justify-center gap-1 py-2.5 text-xs font-semibold leading-tight transition-colors md:gap-0.5 md:py-2 md:text-[10px] ${
```

```diff
-                      className={`flex h-7 w-7 items-center justify-center rounded-full transition-colors ${
+                      className={`flex h-9 w-9 items-center justify-center rounded-full transition-colors md:h-7 md:w-7 ${
                         isActive ? "bg-green-100" : ""
                       }`}
                     >
-                      <Icon className="h-5 w-5" />
+                      <Icon className="h-6 w-6 md:h-5 md:w-5" />
```

- **Mobile**: círculo de ícono `h-9 w-9` (36px), ícono `h-6 w-6` (24px),
  texto `text-xs` (12px), `py-2.5` — área táctil sensiblemente mayor.
  `pb-28` en `<main>` para que el contenido no quede tapado por el nav más
  alto.
- **Desktop (`md:`)**: círculo `h-7 w-7`, ícono `h-5 w-5`, texto
  `text-[10px]`, `py-2`, `pb-24` — **idéntico a los valores anteriores**.

### 2.2 Dashboard — "Accesos rápidos" (`Dashboard.jsx`)

```diff
-        <div className="grid grid-cols-2 gap-3">
+        <div className="flex flex-col gap-2 md:grid md:grid-cols-2 md:gap-3">
           <QuickLink to="/buscar" label="Buscar" icon={IconSearch} />
           <QuickLink to="/album" label="Álbum" icon={IconAlbum} />
           <QuickLink to="/faltantes" label="Faltantes" icon={IconAlert} />
           <QuickLink to="/repetidas" label="Repetidas" icon={IconLayers} />
-          <QuickLink to="/cerca" label="Usuarios cerca" icon={IconMapPin} className="col-span-2" />
+          <QuickLink to="/cerca" label="Usuarios cerca" icon={IconMapPin} className="md:col-span-2" />
```

- **Mobile**: los 5 accesos pasan de una grilla 2x2+1 (con una celda vacía)
  a una **lista vertical de ancho completo**: 5 filas, cada una un botón
  grande de ancho total. Elimina la celda vacía y, al ocupar más alto total,
  reduce el espacio vacío que quedaba antes del nav inferior.
- **Desktop (`md:`)**: vuelve a la grilla 2 columnas con "Usuarios cerca"
  ocupando las 2 columnas — **igual que antes**.
- Resto del Dashboard (hero card, tira de banderas, 3 stats) sin cambios.

### 2.3 Álbum — cabecera de `CountryCard` (`Album.jsx`)

```diff
         <div className="min-w-0 flex-1">
           <p className="truncate font-bold text-gray-800">
             {getCountryLabel(country.country_name, country.country_code)}
           </p>
-          <p className="text-sm text-gray-500 md:text-xs">
-            {summary.pegadas}/{summary.total} pegadas
-          </p>
-          <p className="mt-0.5 text-sm md:text-xs">
-            <span className="font-semibold text-faltante">{summary.faltantes} faltantes</span>
-            {" · "}
-            <span className="font-semibold text-yellow-600">{summary.repetidas} repetidas</span>
-          </p>
+          <div className="hidden md:block">
+            <p className="text-xs text-gray-500">
+              {summary.pegadas}/{summary.total} pegadas
+            </p>
+            <p className="mt-0.5 text-xs">
+              <span className="font-semibold text-faltante">{summary.faltantes} faltantes</span>
+              {" · "}
+              <span className="font-semibold text-yellow-600">{summary.repetidas} repetidas</span>
+            </p>
+          </div>
         </div>
         <ProgressRing ...>...</ProgressRing>
       </div>

+      <div className="mt-2 md:hidden">
+        <p className="text-sm text-gray-500">
+          {summary.pegadas}/{summary.total} pegadas
+        </p>
+        <p className="mt-0.5 text-sm">
+          <span className="font-semibold text-faltante">{summary.faltantes} faltantes</span>
+          {" · "}
+          <span className="font-semibold text-yellow-600">{summary.repetidas} repetidas</span>
+        </p>
+      </div>

       <div className="mt-3 grid grid-cols-5 gap-2 md:grid-cols-10 md:gap-1">
         {/* badges, sin cambios — ya agrandados en P1 */}
```

- **Mobile**: la fila superior queda solo con **bandera + nombre + anillo
  de progreso** (más compacta y despejada). El resumen ("X/20 pegadas",
  "Y faltantes · Z repetidas") pasa a su **propia fila de ancho completo**
  debajo, en `text-sm` — usa todo el ancho de la tarjeta en vez de quedar
  apretado entre la bandera y el anillo.
- **Desktop (`md:`)**: el bloque `hidden md:block` reproduce exactamente la
  fila única anterior (bandera + [nombre + resumen apilados] + anillo, todo
  en `text-xs`); el bloque mobile-only se oculta (`md:hidden`).
- Badges (grilla, tamaño, colores) sin cambios — ya resueltos en P1.

### 2.4 Faltantes (`Missing.jsx`) y Repetidas (`Duplicates.jsx`)

Mismo cambio en ambos archivos:

```diff
-          <div className="mt-2 flex flex-wrap gap-2 md:gap-1">
+          <div className="mt-2 grid grid-cols-4 gap-2 md:flex md:flex-wrap md:gap-1">
             {country.numbers.map((number) => (
               <span
                 key={number}
-                className="flex items-center justify-center rounded-full bg-red-50 px-3 py-3 text-sm font-bold text-faltante md:px-2 md:py-1 md:text-xs md:font-semibold"
+                className="flex w-full items-center justify-center rounded-full bg-red-50 px-3 py-3 text-sm font-bold text-faltante md:w-auto md:px-2 md:py-1 md:text-xs md:font-semibold"
               >
                 {number === 0 ? "00" : number}
               </span>
             ))}
           </div>
```

(En `Duplicates.jsx` es el mismo patrón, con `bg-yellow-50 text-yellow-700`
y el formato `N (xQ)`.)

- **Mobile**: contenedor pasa de `flex flex-wrap` (una "fila interminable"
  que reflowea según el ancho del texto) a **`grid grid-cols-4`**: 20
  números → 5 filas de 4. Cada badge ocupa `w-full` dentro de su celda, con
  `px-3 py-3 text-sm font-bold` (ya definido en P1) → grilla regular de
  badges grandes, sin filas largas e impredecibles.
- **Desktop (`md:`)**: `md:flex md:flex-wrap md:gap-1` + badge
  `md:w-auto md:px-2 md:py-1 md:text-xs md:font-semibold` — **reproduce
  exactamente** el `flex-wrap` y tamaños que ya existían (P1).
- Botón "Copiar para WhatsApp" y lógica de "00"/`(xN)` sin cambios.

---

## 3. Resumen: qué cambió en cada breakpoint

| Pantalla | Mobile (sin prefijo) | Desktop (`md:`, ≥768px) |
|---|---|---|
| Nav inferior | 7 ítems, círculo 36px, ícono 24px, texto 12px | 7 ítems, círculo 28px, ícono 20px, texto 10px — **igual que antes** |
| Dashboard | "Accesos rápidos" = lista vertical de 5 filas completas | "Accesos rápidos" = grilla 2 col (5° ítem ocupa 2 col) — **igual que antes** |
| Álbum | Header: bandera+nombre+anillo en fila 1, resumen en fila 2 (ancho completo, `text-sm`) | Header: bandera + [nombre+resumen apilados, `text-xs`] + anillo, una sola fila — **igual que antes** |
| Faltantes/Repetidas | Badges en grilla `grid-cols-4` (4 col x 5 filas para 20 números), `w-full` | Badges en `flex-wrap`, `w-auto` — **igual que antes** |

---

## 4. Build

```
> stickercontrol-2026-frontend@0.1.0 build
> vite build

vite v5.4.21 building for production...
✓ 51 modules transformed.
dist/index.html                 0.52 kB │ gzip:  0.32 kB
dist/assets/index-17O3QMZQ.css  15.63 kB │ gzip:  3.81 kB
dist/assets/index-De83U4L9.js   195.93 kB │ gzip: 61.70 kB
✓ built in 3.09s
```

**Resultado: BUILD OK** (sin errores ni warnings). Se verificó en el CSS
generado (`dist/assets/index-17O3QMZQ.css`) la presencia de
`grid-cols-4`, `.md\:flex`, `.md\:hidden`, `.md\:col-span-2` y el resto de
variantes `md:` introducidas.

## 5. Validación realizada

- Build de producción: OK.
- Rutas vía `vite preview` (`base="/stickercontrol/"`):

| Ruta | Resultado |
|---|---|
| `/stickercontrol/` | `200` |
| `/stickercontrol/buscar` | `200` |
| `/stickercontrol/album` | `200` |
| `/stickercontrol/faltantes` | `200` |
| `/stickercontrol/repetidas` | `200` |
| `/stickercontrol/cerca` | `200` |

- No se ejecutó en Android real en esta sesión. Para validar, recordar el
  hallazgo de `ROOT_CAUSE_ANALYSIS_P1_FAILURE.md`: usar el navegador en modo
  móvil normal (sin "Sitio de escritorio"/zoom forzado) y, si corresponde,
  confirmar que el `dist/` desplegado en el VPS incluye este build
  (`index-17O3QMZQ.css` / `index-De83U4L9.js`).

## 6. Riesgo desktop

Todos los cambios siguen el mismo patrón: las clases sin prefijo definen la
nueva estructura mobile, y cada variante `md:` reproduce el valor/estructura
que existía antes del cambio (mismos tamaños de nav, misma grilla 2 col de
accesos rápidos, mismo header de una fila en Álbum, mismo `flex-wrap` en
Faltantes/Repetidas). Riesgo: **bajo**.

## 7. Próximos pasos

No se avanza a login ni nuevas funciones, según instrucción explícita.
Pendiente (fuera de esta tarea): validar visualmente en Android real con el
navegador en modo móvil normal, y confirmar el estado del deploy en el VPS.
