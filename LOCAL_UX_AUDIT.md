# Auditoría UX local (Fase 0.6.5) — antes del deploy a SkillGames

Prueba funcional de StickerControl 2026 "como un usuario real", corriendo
backend (`uvicorn app.main:app --reload`) y frontend (`npm run dev`) en
local, sin cambios de código ni nuevas funcionalidades.

## 1. Entorno local

- Backend: `uvicorn app.main:app --reload --port 8000` → arranca sin
  errores, `GET /` → `{"status":"ok","app":"StickerControl 2026"}`.
- Frontend: `npm run dev` → arranca sin errores en `http://localhost:5173`.
- Sin errores en consola/terminal durante el recorrido.

## 2. Recorrido completo

Dashboard, Buscar, Álbum, Faltantes, Repetidas, Cerca e Intercambios
revisados (código + llamadas API reales). Ver hallazgos en la sección 8.

## 3. Carga real de figuritas

Se cargó una colección de ejemplo realista contra la base local real
(`backend/stickercontrol.db`), usando los mismos endpoints que usa el
frontend:

- **20 pegadas**: `00`, `FWC1`, `FWC2`, `FWC3`, `ARG1`-`ARG5`, `BRA1`-`BRA4`,
  `MEX1`-`MEX4`, `CZE1`-`CZE3`.
- **5 con repetidas** (subconjunto de las anteriores, vía `+1`): `ARG1`
  (x1), `ARG2` (x1), `BRA1` (x2), `MEX1` (x1), `FWC1` (x1) →
  `PEGADA_CON_REPETIDA` con `repetidas` correctas en cada caso.
- **5 faltantes explícitas** (marcadas con "Marcar faltante"): `ARG10`,
  `BRA10`, `MEX10`, `FWC10`, `CZE10` → quedan en `FALTANTE`.

Verificación de persistencia con `GET /api/reports/album`:
`{"total": 980, "pegadas": 20, "faltantes": 960, "repetidas": 8}` — los 8
repetidas vienen de los 5 códigos cargados ahora (1+1+2+1+1=6) más 2
repetidas de `MEX3` que ya existían de pruebas de fases anteriores. Todo
correcto y persistente entre requests.

- Búsqueda por código exacto (`MEX1`, `ARG1`, `00`, `FWC1`, etc.) encuentra
  la figurita correcta.
- "Pegar"/"Despegar", `+1`/`-1` y "Marcar faltante" actualizan el estado al
  instante y quedan guardados en SQLite.

## 4. Flujo de coleccionista

- **¿Puedo cargar figuritas rápido?** Sí para códigos de 2 dígitos
  (`ARG10`, `MEX10`: 1 resultado exacto). Para códigos de 1 dígito
  (`ARG1`, `MEX1`, `FWC1`...) la búsqueda por substring devuelve **11
  resultados** (`ARG1`, `ARG10`-`ARG19`), aunque el resultado exacto
  (`ARG1`) aparece primero en la lista por orden alfabético. Es decir: 1
  búsqueda + 1 click sigue funcionando, pero se ve una lista más larga de
  lo necesario.
- **¿Cuántos clics necesito?** Buscar (1 submit) + acción (1 click) por
  figurita ≈ 2 acciones. Para repetidas: 1 click extra (`+1`).
- **¿Hay pasos innecesarios?** No para el flujo principal
  (Buscar → Pegar/+1/Marcar faltante). El Álbum es de **solo lectura** (no
  se puede tocar una figurita ahí para cambiar su estado) — si el usuario
  ve un error en el Álbum, tiene que volver a Buscar para corregirlo.
- **¿Hay algo que me haga volver atrás?** Solo el punto anterior (Álbum
  read-only). El resto del flujo es lineal.
- **¿Entiendo inmediatamente qué hacer?** Sí: la nueva landing del
  Dashboard ("Controlá tus figuritas del Mundial 2026" + botón "Empezar")
  lleva directo a Buscar, y cada tarjeta de figurita tiene botones grandes
  y autoexplicativos (Pegar/Despegar, +1, -1, Marcar faltante).

## 5. Faltantes y repetidas

- `GET /api/reports/duplicates` →
  `text` = `"REPETIDAS:\nARG: 1, 2\nBRA: 1(x2)\nFWC: 1\nMEX: 1, 3(x2)"` —
  formato correcto, `(xN)` solo cuando `quantity > 1`.
- `GET /api/reports/missing` → `text` empieza con `"FALTANTES:\nALG: 1,
  2, ..., 20\n..."`, 49 países, **3624 caracteres** en total (con solo 20
  figuritas pegadas de 980). El formato es correcto y claro, pero para un
  usuario que recién empieza el texto de faltantes es muy largo (resumen
  casi completo del álbum). No es un error — a medida que se carga la
  colección real, el texto se acorta — pero conviene tenerlo en cuenta.
- Botón "Copiar para WhatsApp" con feedback "¡Copiado!" funciona en ambas
  páginas (verificado a nivel de código: usa `navigator.clipboard` +
  `data.text` del backend).

## 6. Usuarios cerca

Probado contra la base real (perfil propio) + un usuario temporal creado
solo para la prueba (eliminado al finalizar):

- `PATCH /api/profile` con nombre, ciudad y ubicación → se guarda y
  persiste; las coordenadas se redondean por privacidad
  (`-34.6037 → -34.6`, `-58.3816 → -58.38`).
- `GET /api/nearby` con un vecino público de prueba → devuelve
  `distance_km` (1.4 km), `match_count` (8), `has_email`/`has_whatsapp`
  (sin exponer los datos de contacto en texto plano, confirmado en
  Fase 0.6.2).
- `GET /api/nearby/{id}/contact-message` → genera el texto con mis
  figuritas reales cargadas (`"A mi me interesan: ARG10, BRA10"` /
  `"Yo tengo repetidas que quizas te sirven: ARG1, ARG2, BRA1, FWC1, MEX1,
  MEX3"`) + `whatsapp_url` y `mailto_url` correctamente codificados.
- Con un solo usuario real (yo), `/api/nearby` devuelve `{"users": []}` y
  el frontend muestra el mensaje "Todavía no hay otros usuarios públicos
  cerca..." — esperado y documentado (no se puede probar el "encuentro"
  real hasta que haya más usuarios).

## 7. Prueba móvil

- `npm run dev -- --host` expone Vite en `http://192.168.100.18:5173`
  (verificado: responde `200` y el proxy `/api` funciona desde esa IP).
- `index.html` incluye `<meta name="viewport" content="width=device-width,
  initial-scale=1.0">`.
- Revisión de clases responsive: `StickerCard` usa
  `grid-cols-2 sm:grid-cols-4` con botones `py-3` (buen tamaño de toque);
  `Album` usa `grid-cols-8 sm:grid-cols-10` con celdas de `h-8` (32px,
  apretadas pero son solo lectura); el nav inferior usa `grid-cols-7` con
  `text-xs` — en pantallas angostas (~320-360px) etiquetas de 9 caracteres
  ("Faltantes", "Repetidas") pueden quedar muy ajustadas o partirse en dos
  líneas.
- **No se pudo verificar visualmente desde un celular real** (sin acceso a
  navegador/dispositivo desde este entorno). Para completar este punto:
  conectar el celular a la misma red WiFi y abrir
  `http://192.168.100.18:5173` mientras `npm run dev -- --host` está
  corriendo, y revisar especialmente el nav inferior y el Álbum.

## 8. Hallazgos clasificados

### ALTO

Ninguno. No se encontraron errores ni bloqueos que impidan usar la app
para su propósito (controlar pegadas/faltantes/repetidas y generar listas
para WhatsApp).

### MEDIO

1. **Álbum es de solo lectura.** Ver una figurita mal marcada en `/album`
   no permite corregirla ahí — hay que ir a `/buscar` y buscar el código de
   nuevo. Es un viaje de ida y vuelta innecesario para correcciones rápidas.
2. **Búsqueda sin filtros por grupo/país/tipo en el frontend.** El backend
   soporta `group`, `country_code`, `type` (ver README), pero `Buscar` solo
   tiene un campo de texto libre. Para cargar muchas figuritas de un mismo
   país de una sola vez, no hay forma de listarlas todas juntas sin
   escribir cada código.
3. **Nav inferior con 7 ítems en `text-xs`.** Pendiente confirmar en un
   celular real que "Faltantes"/"Repetidas"/"Intercambios" no se corten o
   amontonen en pantallas angostas (~320px).

### BAJO

1. **Búsqueda por código de 1 dígito devuelve resultados extra** (`ARG1` →
   11 resultados, incluye `ARG10`-`ARG19`), aunque el resultado exacto
   aparece primero. Solo afecta la "limpieza visual" de la lista, no el
   flujo (sigue siendo 1 click sobre el primer resultado).
2. **Dashboard no enlaza directamente a "Cerca"** desde los accesos rápidos
   (solo Buscar/Álbum/Faltantes/Repetidas) — se llega por el nav inferior,
   pero es la función más nueva y podría destacarse más.
3. **Texto de "Faltantes" muy largo al empezar** (3624 caracteres con solo
   20/980 pegadas) — correcto pero abrumador para un usuario nuevo; se
   normaliza a medida que avanza la colección.
4. **"Intercambios" sigue como "Próximamente"** ocupando un lugar en el nav
   — decisión de producto ya documentada (`NEARBY_USERS_MVP.md`), pero un
   usuario nuevo podría tocarlo esperando algo funcional.
5. **"Usuarios cerca" no se puede validar de punta a punta con un solo
   usuario real** — esperado en este entorno (single-user), no es un
   defecto de la implementación.

### Funciona bien (para destacar)

- Arranque limpio de backend y frontend, sin errores.
- Ciclo completo Buscar → Pegar/+1/-1/Marcar faltante → persistencia en
  SQLite, verificado con datos reales (20 pegadas, 8 unidades repetidas en
  5 códigos, 5 faltantes explícitas).
- Álbum con resumen por país, colores de estado y porcentaje de avance.
- Faltantes/Repetidas con texto WhatsApp correcto y botón de copiar con
  feedback.
- Usuarios cerca: perfil con redondeo de ubicación (privacidad), `/api/nearby`
  sin exponer contacto en texto plano, `contact-message` con mensaje +
  links de WhatsApp/email generados en el servidor con datos reales de mi
  colección.
- Landing del Dashboard (Fase 0.6.2) clara y con llamada a la acción.
- `npm run dev -- --host` funciona para acceso desde la red local (listo
  para prueba móvil real).

## 9. Decisión final

**B) Requiere ajustes menores.**

La aplicación cumple su propósito: permite cargar y mantener al día una
colección real (pegadas/faltantes/repetidas) y generar listas claras para
compartir por WhatsApp, y "Usuarios cerca" funciona técnicamente de punta a
punta (perfil, matching, mensaje, links). No se encontró ningún error ni
bloqueo (ALTO = 0).

Los puntos MEDIO (Álbum solo lectura, falta de filtros de búsqueda por
grupo/país, nav inferior a confirmar en celular real) no impiden el deploy
a SkillGames, pero son las primeras candidatas para una futura iteración de
UX — ninguno requiere cambios de arquitectura ni nuevas funcionalidades,
serían ajustes acotados dentro de las pantallas existentes.
