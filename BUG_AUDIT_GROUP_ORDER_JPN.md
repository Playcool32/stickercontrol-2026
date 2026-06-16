# Auditoría de bugs: JPN y orden de grupos H/I/L

**Fecha:** 2026-06-15  
**Estado:** Diagnóstico únicamente — sin cambios de código todavía.

---

## 1. Dónde aparece JAP / JAN / JPN

### `JAP` (código incorrecto — debe ser `JPN`)

| Archivo | Línea(s) | Contenido |
|---|---|---|
| `data/countries.json` | 201, 205 | `"fifa_code": "JAP"` y `"flag_path": "/flags/JAP.png"` |
| `data/stickers_master.csv` | 442–461 | 20 filas: `code=JAP1..JAP20`, `country_code=JAP` |
| `backend/stickercontrol.db` | `master_stickers` id 485–504 | 20 filas con `country_code='JAP'`, `code='JAP1'..'JAP20'` |
| `frontend/public/flags/JAP.png` | — | Archivo de bandera con nombre incorrecto |

### `JPN` — no existe en ninguna parte del proyecto

No hay ningún archivo, tabla, columna ni referencia al código correcto `JPN`.

### `JAN` — no existe en ninguna parte del proyecto

No se encontró ninguna referencia a `JAN`.

### Referencias en documentos históricos (solo texto, sin impacto en runtime)

Los siguientes `.md` mencionan `JAP` como parte de registros de fases anteriores.
No generan bugs por sí solos, pero quedarán desactualizados si se migra el código:

- `GROUP_ORDER_AUDIT.md` — tablas de ejemplo (líneas 65, 93, 163, 306)
- `GROUP_ORDER_IMPLEMENTATION_REPORT.md` — lista verificada "Faltantes" (líneas 97, 113)
- `NEARBY_FORENSIC_TEST.md` — datos de prueba temporales ya no activos (líneas 15, 48, 50, 96, 159, 171, 201, 226)
- `IMPORT_MASTER_STICKERS_REPORT.md` — tabla de conteo por selección (línea 56)

---

## 2. Qué archivos están mal

### Bug A: código `JAP` → debe ser `JPN`

| Archivo | Tipo | Está mal | Impacto en runtime |
|---|---|---|---|
| `data/countries.json` | Fuente de datos | `fifa_code: "JAP"`, `flag_path: "/flags/JAP.png"` | Sí — `load_countries()` indexa por `fifa_code`, así que el lookup `JPN` devolvería `None` (sin bandera, sin `album_order`) si se buscara con el código correcto |
| `data/stickers_master.csv` | Fuente de seed | `code` y `country_code` con prefijo `JAP` | Sí — si se re-ejecuta `seed_db.py` desde el CSV sin corregirlo, la migración genera 20 filas nuevas `JPN*` + elimina las `JAP*`, rompiendo integridad si hubiera `user_stickers` |
| `backend/stickercontrol.db` | Base de datos | `master_stickers.country_code='JAP'`, `master_stickers.code='JAP1'..'JAP20'` | Sí — los codes y el country_code que ve el usuario en UI y WhatsApp son `JAP*` |
| `frontend/public/flags/JAP.png` | Asset estático | Nombre del archivo incorrecto | Sí — si se cambia el `flag_path` en `countries.json` a `/flags/JPN.png`, la bandera deja de servirse hasta que el archivo se renombre |

### Bug B: `album_order` incorrecto en grupos H, I y L

| Archivo | Tipo | Está mal |
|---|---|---|
| `data/countries.json` | Fuente de datos | `album_order` de 9 países en grupos H, I, L — ver tabla abajo |

---

## 3. Qué tabla/CSV/JSON controla el orden del álbum

El orden dentro de cada grupo en el Álbum (y en Faltantes/Repetidas) está controlado **exclusivamente** por:

```
data/countries.json  →  campo "album_order" (int 1-4)
    ↓  leído por
backend/app/countries.py  →  get_album_order(fifa_code)
    ↓  usado en
backend/app/routes/reports.py  →  key=lambda item: get_album_order(item[0])
    ↓  orden final del JSON
frontend/src/pages/Album.jsx  →  consume la respuesta tal cual, sin reordenar
```

No hay lógica de ordenamiento en el frontend ni en `master_stickers`. El CSV y la DB no afectan el orden (solo proveen los stickers; el orden lo da `countries.json`).

---

## 4. Errores exactos en `album_order` (grupos H, I, L)

### Situación actual vs. oficial Panini

**Grupo H — estado actual en `countries.json`:**

| País | `album_order` actual | Orden actual que muestra la app |
|---|---|---|
| CPV | 1 | 1° |
| KSA | 2 | 2° |
| ESP | 3 | 3° |
| URU | 4 | 4° |

**Resultado actual:** `CPV, KSA, ESP, URU`  
**Correcto según índice oficial Panini:** `ESP, CPV, KSA, URU`

**Corrección necesaria:**

| País | `album_order` actual | `album_order` correcto |
|---|---|---|
| ESP | 3 | **1** |
| CPV | 1 | **2** |
| KSA | 2 | **3** |
| URU | 4 | 4 (sin cambio) |

---

**Grupo I — estado actual en `countries.json`:**

| País | `album_order` actual | Orden actual que muestra la app |
|---|---|---|
| FRA | 1 | 1° |
| IRQ | 2 | 2° |
| NOR | 3 | 3° |
| SEN | 4 | 4° |

**Resultado actual:** `FRA, IRQ, NOR, SEN`  
**Correcto según índice oficial Panini:** `FRA, SEN, IRQ, NOR`

**Corrección necesaria:**

| País | `album_order` actual | `album_order` correcto |
|---|---|---|
| FRA | 1 | 1 (sin cambio) |
| SEN | 4 | **2** |
| IRQ | 2 | **3** |
| NOR | 3 | **4** |

---

**Grupo L — estado actual en `countries.json`:**

| País | `album_order` actual | Orden actual que muestra la app |
|---|---|---|
| ENG | 1 | 1° |
| CRO | 2 | 2° |
| PAN | 3 | 3° |
| GHA | 4 | 4° |

**Resultado actual:** `ENG, CRO, PAN, GHA`  
**Correcto según índice oficial Panini:** `ENG, CRO, GHA, PAN`

**Corrección necesaria:**

| País | `album_order` actual | `album_order` correcto |
|---|---|---|
| ENG | 1 | 1 (sin cambio) |
| CRO | 2 | 2 (sin cambio) |
| GHA | 4 | **3** |
| PAN | 3 | **4** |

---

## 5. Contexto histórico (por qué está mal)

En `GROUP_ORDER_AUDIT.md` se documentó que el orden del CSV/JSON para los grupos H, I y L
**no coincidía** con la "fuente de verdad" que se tenía en ese momento.
La tabla del audit decía:

| Grupo | Orden CSV/JSON | "Fuente de verdad" anterior | ¿Coincide? |
|---|---|---|---|
| H | ESP, CPV, KSA, URU | CPV, KSA, ESP, URU | ❌ |
| I | FRA, SEN, IRQ, NOR | FRA, IRQ, NOR, SEN | ❌ |
| L | ENG, CRO, GHA, PAN | ENG, CRO, PAN, GHA | ❌ |

Se implementó la "fuente de verdad anterior" en `album_order`, pero esa fuente
**también era incorrecta**. El índice oficial del álbum Panini WC 2026 da:

| Grupo | Orden oficial Panini |
|---|---|
| H | ESP, CPV, KSA, URU |
| I | FRA, SEN, IRQ, NOR |
| L | ENG, CRO, GHA, PAN |

Casualmente, el orden **oficial Panini coincide con el orden original del CSV/JSON**
para estos tres grupos. La implementación anterior sobre-escribió el orden correcto
con valores incorrectos.

---

## 6. Si hace falta tocar DB o solo datos fuente

### Bug A (JAP → JPN)

**Sí hace falta tocar la DB.** La tabla `master_stickers` tiene 20 filas con
`country_code='JAP'` y `code='JAP1'..'JAP20'`. Si no se toca la DB, la app sigue
mostrando `JAP` en la UI aunque el CSV y el JSON se corrijan (el backend sirve los
datos de la DB, no del CSV directamente).

El enfoque recomendado (igual que la migración `FW* → FWC*`) es:
- `UPDATE master_stickers` in-place (cambia `code` y `country_code`, preserva `id`)
- Actualizar `data/countries.json` (cambiar `fifa_code` y `flag_path`)
- Actualizar `data/stickers_master.csv` (cambiar `code` y `country_code` en las 20 filas)
- Renombrar `frontend/public/flags/JAP.png` → `JPN.png`
- **No ejecutar** `seed_db.py` (los `id` 485-504 se preservan con el UPDATE in-place)

**Riesgo de `user_stickers`:** NINGUNO. Verificado en la DB local: hay **0 filas**
en `user_stickers` que referencien stickers JAP. La migración no puede romper
colecciones de usuarios.

### Bug B (album_order grupos H, I, L)

**No hace falta tocar la DB.** El `album_order` se lee de `data/countries.json`
en tiempo de ejecución (cacheado con `@lru_cache`). Corregir los valores en ese
archivo es suficiente.

Hay que vaciar el cache de `load_countries()` al reiniciar el backend (el `lru_cache`
de Python se borra al reiniciar el proceso, no hace falta código adicional).

---

## 7. Cambios mínimos necesarios

### Para Bug A (JAP → JPN)

1. **`data/countries.json`** — 1 entrada, 2 campos:
   - `"fifa_code": "JAP"` → `"fifa_code": "JPN"`
   - `"flag_path": "/flags/JAP.png"` → `"flag_path": "/flags/JPN.png"`

2. **`data/stickers_master.csv`** — 20 filas (la columna `code` y la columna `country_code`):
   - `JAP1,F,JAP,...` → `JPN1,F,JPN,...`
   - ... (JAP2-JAP20 igual)

3. **`backend/stickercontrol.db`** — 2 updates in-place (sin tocar `id` ni `user_stickers`):
   ```sql
   UPDATE master_stickers SET code = 'JPN' || substr(code, 4) WHERE country_code = 'JAP';
   UPDATE master_stickers SET country_code = 'JPN' WHERE country_code = 'JAP';
   ```
   (20 filas afectadas en cada UPDATE; ids 485–504 se preservan)

4. **`frontend/public/flags/JAP.png`** — renombrar a `JPN.png`
   (misma imagen, solo nombre corregido)

5. **`seed_db.py`** — **NO ejecutar** (UPDATE in-place ya deja la DB sincronizada con el CSV corregido)

6. **Documentos históricos** — NO actualizar ahora (son registros de fases pasadas; su actualización es opcional y cosmética, no afecta runtime)

### Para Bug B (album_order grupos H, I, L)

1. **`data/countries.json`** — 6 entradas, campo `album_order`:

   | `fifa_code` | Valor actual | Valor correcto |
   |---|---|---|
   | ESP | 3 | 1 |
   | CPV | 1 | 2 |
   | KSA | 2 | 3 |
   | URU | 4 | 4 (sin cambio) |
   | SEN | 4 | 2 |
   | IRQ | 2 | 3 |
   | NOR | 3 | 4 |
   | FRA | 1 | 1 (sin cambio) |
   | GHA | 4 | 3 |
   | PAN | 3 | 4 |
   | ENG | 1 | 1 (sin cambio) |
   | CRO | 2 | 2 (sin cambio) |

   En la práctica: 6 cambios reales (ESP, CPV, KSA, SEN, IRQ, NOR, GHA, PAN — excluidos los "sin cambio").

2. **Reiniciar el backend** para que `lru_cache` de `load_countries()` se invalide.

3. **Sin cambios** en: `backend/app/countries.py`, `backend/app/routes/reports.py`, frontend, DB, CSV.

---

## 8. Riesgos

| Riesgo | Nivel | Mitigación |
|---|---|---|
| `user_stickers` con codes `JAP*` quedan huérfanos | **NULO** — confirmado 0 filas en la DB local | N/A |
| Renombrar flag `JAP.png` → `JPN.png` rompe la imagen si el cambio en `countries.json` y el rename no se hacen juntos | Bajo | Hacer ambos en la misma operación antes de reiniciar backend |
| `lru_cache` de `load_countries()` sirve datos viejos si el backend NO se reinicia | Bajo | Reiniciar el proceso uvicorn después de cambiar `countries.json` |
| Typo en algún `album_order` deja un grupo desordenado | Bajo | Verificar con el script de validación después de aplicar |
| La DB de producción (VPS) tiene `user_stickers` de JAP | Desconocido | Ver sección 9 — verificar en producción antes de aplicar |

### Riesgo especial: producción vs. local

La DB local tiene 0 filas en `user_stickers` para JAP. Pero la DB de producción
(`skillgames.com.ar/stickercontrol`) puede tener usuarios reales que pegaron/marcaron
figuritas de Japón. Antes de aplicar la migración en producción hay que verificar:

```sql
SELECT COUNT(*) FROM user_stickers us
JOIN master_stickers ms ON us.sticker_id = ms.id
WHERE ms.country_code = 'JAP' AND (us.quantity > 0 OR us.is_pasted = 1);
```

Si el resultado es > 0, el UPDATE in-place de `master_stickers` sigue siendo seguro
(cambia `code` y `country_code`, no toca `sticker_id` ni la FK de `user_stickers`),
pero los usuarios verán sus figuritas de "JAP" renombradas a "JPN" — que es justamente
el objetivo correcto.

---

## 9. Plan exacto de implementación

### Orden de operaciones

```
PASO 1 (datos fuente, sin tocar DB ni código):
  a. data/countries.json — corregir fifa_code JAP→JPN, flag_path JAP.png→JPN.png
  b. data/countries.json — corregir album_order de grupos H, I, L (6 cambios)
  c. data/stickers_master.csv — corregir 20 filas (code y country_code JAP→JPN)

PASO 2 (DB local — UPDATE in-place, sin seed_db.py):
  a. Hacer backup de stickercontrol.db antes de tocar
  b. UPDATE master_stickers: code JAP*→JPN*
  c. UPDATE master_stickers: country_code JAP→JPN

PASO 3 (asset estático):
  a. Copiar/renombrar frontend/public/flags/JAP.png → JPN.png

PASO 4 (verificación local):
  a. Reiniciar backend (invalida lru_cache)
  b. Verificar /api/reports/album:
     - Grupo F: NED, JPN, SWE, TUN (no JAP)
     - Grupo H: ESP, CPV, KSA, URU
     - Grupo I: FRA, SEN, IRQ, NOR
     - Grupo L: ENG, CRO, GHA, PAN
  c. Verificar /api/stickers/search?q=JPN1 → 1 resultado
  d. Verificar /api/stickers/search?q=JAP1 → 0 resultados
  e. Verificar bandera de Japón visible en Álbum (JPN.png servido)
  f. Confirmar master_stickers: 980 filas, 0 con country_code='JAP', 20 con 'JPN'
  g. Confirmar user_stickers: mismo conteo antes/después

PASO 5 (producción — solo cuando local esté verificado):
  a. Backup de DB productiva antes de tocar
  b. Mismo UPDATE in-place en la DB del VPS
  c. Actualizar los archivos (countries.json, stickers_master.csv, JPN.png)
  d. Reiniciar backend en el VPS
```

### Archivos a tocar

| Archivo | Cambio |
|---|---|
| `data/countries.json` | `fifa_code`, `flag_path` de JAP; `album_order` de 8 países (H/I/L) |
| `data/stickers_master.csv` | 20 filas: `code` y `country_code` JAP→JPN |
| `backend/stickercontrol.db` | UPDATE in-place (no seed_db.py) |
| `frontend/public/flags/JAP.png` | Renombrar a `JPN.png` |

**Total: 4 archivos + 1 DB update.**

---

## 10. Confirmación de lo que NO se toca

| Componente | Estado |
|---|---|
| Google Login / auth (`backend/app/auth.py`, `/api/auth`, `AuthContext`, `PrivateRoute`) | **NO SE TOCA** |
| Responsive / mobile (Layout, Album, Missing, Duplicates, Dashboard) | **NO SE TOCA** |
| Rutas frontend (`App.jsx`, `vite.config.js`, `main.jsx`) | **NO SE TOCA** |
| nginx / VPS / systemd | **NO SE TOCA** |
| Diseño visual (colores, badges, ProgressRing, StickerDetailModal) | **NO SE TOCA** |
| Lógica de colección (`status.py`, paste/unpaste/increment/decrement) | **NO SE TOCA** |
| `backend/app/routes/reports.py` | **NO SE TOCA** (el ordenamiento ya usa `get_album_order`, solo cambia el JSON fuente) |
| `backend/app/countries.py` | **NO SE TOCA** (la función `get_album_order` ya existe y funciona) |
| `seed_db.py` | **NO SE EJECUTA** (update in-place en DB, no se re-siembra) |
| `user_stickers` | **NO SE TOCA** (0 filas JAP en DB local; UPDATE in-place preserva los `sticker_id`) |
| Documentos históricos (`GROUP_ORDER_AUDIT.md`, `GROUP_ORDER_IMPLEMENTATION_REPORT.md`, etc.) | **NO SE TOCAN** (son registros históricos; actualización cosmética opcional, post-implementación) |
