# Auditoría: orden real del Álbum (grupos y selecciones)

Estado: **auditoría únicamente, sin cambios de código**.

## 1. De dónde sale hoy el orden

### Grupos (A-L)

- En `backend/app/routes/reports.py::get_album()`, los grupos se ordenan con
  `sorted(groups.items())` → orden alfabético de la letra de grupo (A, B, C...
  L).
- Para este álbum, **el orden alfabético A-L coincide con el orden real del
  sorteo** (los grupos se llaman A-L en ese mismo orden). No hay problema
  aquí. **No se necesita `group_order`.**

### Selecciones dentro de cada grupo (el problema real)

- `data/stickers_master.csv` y `data/countries.json` tienen sus filas/entradas
  en un orden de inserción fijo (viene del Excel `StickerAlbumWC2026.xlsm`
  importado por `scripts/import_master_stickers_from_xlsm.py`).
- Pero **ese orden de inserción NO es el que se usa en la respuesta de la
  API**. En `reports.py::get_album()`:

  ```python
  countries=[build_country(cc, data) for cc, data in sorted(countries.items())]
  ```

  `countries` es un dict `country_code -> datos`. `sorted(countries.items())`
  ordena por **`country_code` alfabéticamente**, descartando el orden de
  inserción del CSV/JSON.
- Lo mismo ocurre en `get_missing()` y `get_duplicates()`:
  `for country_code, data in sorted(by_country.items())` (alfabético).
- `/api/stickers/search` (`stickers.py`) usa
  `order_by(MasterSticker.country_code, MasterSticker.number)` → también
  alfabético por `country_code`.

### SQLite / `master_stickers`

- `master_stickers.id` (autoincrement) sigue el orden de filas del CSV (orden
  del Excel original), porque `seed_db.py` inserta en el orden del CSV.
- Pero ningún endpoint usa `id` ni el orden del CSV para ordenar la salida:
  todos re-ordenan explícitamente (`order_by(country_code, number)` o
  `sorted(...)` por `country_code`).

### Frontend

- `Album.jsx` y `Dashboard.jsx` **no reordenan nada**: consumen
  `album.groups[].countries[]` y `album.special[]` tal cual los devuelve la
  API, en el orden que venga.
- Conclusión: el problema está **100% en el backend** (`reports.py` y, si se
  quiere extender, `stickers.py`). El frontend no necesita tocarse para el
  caso principal (Álbum/Dashboard).

## 2. Confirmación empírica del orden alfabético accidental

Respuesta real de `/api/reports/album` (orden actual, alfabético por
`country_code` dentro de cada grupo):

```
A -> CZE, KOR, MEX, RSA
B -> BIH, CAN, QAT, SUI
C -> BRA, HAI, MAR, SCO
D -> AUS, PAR, TUR, USA
E -> CIV, CUW, ECU, GER
F -> JAP, NED, SWE, TUN
G -> BEL, EGY, IRN, NZL
H -> CPV, ESP, KSA, URU
I -> FRA, IRQ, NOR, SEN
J -> ALG, ARG, AUT, JOR
K -> COD, COL, POR, UZB
L -> CRO, ENG, GHA, PAN
special -> FWC
```

Comparado con la fuente de verdad que diste, **ningún grupo coincide
actualmente** (salvo que algunas selecciones queden "casualmente" en el lugar
correcto). Ejemplo Grupo A: hoy `CZE, KOR, MEX, RSA` (alfabético) vs. real
`MEX, RSA, KOR, CZE`.

## 3. Comparación CSV/`countries.json` (orden de inserción) vs. fuente de verdad

El orden de inserción de `data/countries.json` / `data/stickers_master.csv`
(heredado del Excel) **no es alfabético**, pero tampoco coincide 100% con la
fuente de verdad que diste:

| Grupo | Orden CSV/JSON actual | Orden real (tu fuente de verdad) | ¿Coincide? |
|---|---|---|---|
| A | MEX, RSA, KOR, CZE | MEX, RSA, KOR, CZE | ✅ |
| B | CAN, BIH, QAT, SUI | CAN, BIH, QAT, SUI | ✅ |
| C | BRA, MAR, HAI, SCO | BRA, MAR, HAI, SCO | ✅ |
| D | USA, PAR, AUS, TUR | USA, PAR, AUS, TUR | ✅ |
| E | GER, CUW, CIV, ECU | GER, CUW, CIV, ECU | ✅ |
| F | NED, JAP, SWE, TUN | NED, JAP, SWE, TUN | ✅ |
| G | BEL, EGY, IRN, NZL | BEL, EGY, IRN, NZL | ✅ |
| H | ESP, CPV, KSA, URU | CPV, KSA, ESP, URU | ❌ |
| I | FRA, SEN, IRQ, NOR | FRA, IRQ, NOR, SEN | ❌ |
| J | ARG, ALG, AUT, JOR | ARG, ALG, AUT, JOR | ✅ |
| K | POR, COD, UZB, COL | POR, COD, UZB, COL | ✅ |
| L | ENG, CRO, GHA, PAN | ENG, CRO, PAN, GHA | ❌ |

**Conclusión importante:** ni el orden alfabético actual de la API, ni el
orden de inserción del CSV/JSON, son una fuente de verdad completa. Hace
falta **codificar explícitamente** el orden 1-4 por grupo que diste, en algún
dato persistente. No se puede "recuperar" automáticamente desde lo que ya
existe.

## 4. Campo nuevo recomendado: `album_order`

Propuesta de nombres y por qué:

- ❌ `group_order`: no hace falta, A-L ya está correcto.
- ❌ `country_order`: ambiguo (¿orden global de países? ¿orden alfabético?).
- ✅ **`album_order`** (entero 1-4): posición de la selección **dentro de su
  grupo**, según el orden real del álbum/sorteo. Nombre descriptivo y no
  choca con nada existente.

Valor: entero `1..4` por cada una de las 48 selecciones (no aplica a `FWC`,
que es la única entrada de `special` y no necesita orden).

## 5. Archivo fuente de verdad recomendado

**Recomendación: agregar el campo `album_order` directamente en
`data/countries.json`**, una entrada por país (las 48 selecciones; FWC se
deja sin el campo o en `null`).

Por qué este archivo y no otra opción:

| Opción | Evaluación |
|---|---|
| **`data/countries.json` + campo `album_order`** ✅ | Ya es "metadata de país" (nombre, bandera, grupo). Agregar un campo más es 100% aditivo. Ya existe el loader cacheado `backend/app/countries.py::load_countries()`. **No requiere migración de SQLite, no toca `master_stickers`, no toca `user_stickers`, no cambia `id`/`code`.** |
| `data/stickers_master.csv` + columna nueva | Requiere agregar la columna en **981 filas** (20 filas por selección), volver a correr `seed_db.py`, y aunque el upsert por `code` preserva `id`/FK de `user_stickers`, es mucho más superficie de cambio para el mismo resultado. |
| `data/group_order.json` (archivo nuevo) | Funciona, pero crea un segundo archivo de metadata de país en paralelo a `countries.json` para un dato que es, conceptualmente, lo mismo tipo de información (atributo por `fifa_code`). Más mantenimiento sin beneficio real. |
| Campo nuevo en `master_stickers` (tabla) | Requiere `ALTER TABLE` / migración SQLite, cambios en `models.py`, `crud.py`, `schemas.py`, re-seed. Mayor riesgo para un dato que es puramente de presentación/orden. |
| Tabla nueva | Sobre-ingeniería para 48 valores fijos que no cambian con la colección del usuario. |

`countries.json` gana porque **ya es la fuente de verdad de metadata de país**
(incluye `group`, que es justamente el otro campo de "orden"), ya tiene
loader+cache, y el cambio es aditivo y reversible sin tocar la base de datos.

### Forma propuesta del campo

```json
{
  "fifa_code": "MEX",
  "iso_code": "MX",
  "group": "A",
  "album_order": 1,
  "name": "Mexico",
  "flag_path": "/flags/MEX.png",
  "flag_source_url": "..."
}
```

Tabla completa de valores `album_order` a aplicar (según tu fuente de verdad):

| Grupo | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| A | MEX | RSA | KOR | CZE |
| B | CAN | BIH | QAT | SUI |
| C | BRA | MAR | HAI | SCO |
| D | USA | PAR | AUS | TUR |
| E | GER | CUW | CIV | ECU |
| F | NED | JAP | SWE | TUN |
| G | BEL | EGY | IRN | NZL |
| H | CPV | KSA | ESP | URU |
| I | FRA | IRQ | NOR | SEN |
| J | ARG | ALG | AUT | JOR |
| K | POR | COD | UZB | COL |
| L | ENG | CRO | PAN | GHA |

(H, I y L son los 3 grupos donde el valor difiere del orden actual del CSV/JSON.)

## 6. Pantallas afectadas

| Pantalla | ¿Usa orden de país dentro de grupo? | Impacto del fix |
|---|---|---|
| **Álbum** | Sí — `album.groups[].countries[]` | Se corrige automáticamente al cambiar el `sorted()` en `get_album()`. Frontend sin cambios. |
| **Dashboard** | Sí, indirectamente — la tira de banderas usa `data.groups.flatMap(g => g.countries)` | Se corrige automáticamente (mismo `/api/reports/album`). Frontend sin cambios. |
| **Faltantes** (`/api/reports/missing`) | Sí — `sorted(by_country.items())` es alfabético | No es parte del problema descrito (Álbum), pero tiene el mismo "alfabetismo accidental". Se puede dejar igual o aplicar la misma clave `album_order` para consistencia (opcional, Fase 2). |
| **Repetidas** (`/api/reports/duplicates`) | Igual que Faltantes | Igual que Faltantes (opcional, Fase 2). |
| **Buscar** (`/api/stickers/search`) | Sí — `order_by(country_code, number)` a nivel SQL, con `offset`/`limit` para paginar | Cambiarlo requiere ordenar en Python por `album_order` **antes** de paginar (dataset total ~980 filas, viable), o agregar columna a `master_stickers` (más invasivo). **No es necesario para el pedido actual** (Buscar no agrupa por país visualmente de la misma manera). Se documenta como decisión separada, no incluida en el fix mínimo. |

**Resumen:** el fix mínimo (Álbum + Dashboard) **no toca el frontend** y se
limita a 2 archivos backend + 1 archivo de datos.

## 7. Plan recomendado (migración más simple)

1. **`data/countries.json`**: agregar `"album_order": <1-4>` a cada una de las
   48 selecciones, según la tabla de la sección 5. La entrada `FWC` no se
   modifica (no tiene `group`, no participa de este orden).

2. **`backend/app/countries.py`**: agregar una función
   `get_album_order(fifa_code: str) -> int` que devuelva
   `load_countries().get(fifa_code, {}).get("album_order", 99)` (default alto
   para que cualquier país sin valor quede al final, sin romper si falta
   algo).

3. **`backend/app/routes/reports.py`** — `get_album()`: cambiar

   ```python
   countries=[build_country(cc, data) for cc, data in sorted(countries.items())]
   ```

   por

   ```python
   countries=[
       build_country(cc, data)
       for cc, data in sorted(countries.items(), key=lambda item: get_album_order(item[0]))
   ]
   ```

   (import adicional: `from ..countries import get_album_order` — ya se
   importa `get_flag_path` de ese mismo módulo).

   El bucle de grupos (`sorted(groups.items())`) **no se toca** (A-L ya es
   correcto). `special_results` (`sorted(special.items())`) tampoco necesita
   cambios: solo tiene `FWC`.

4. **Opcional / Fase 2** (no incluido en el fix mínimo, a decidir):
   - Aplicar la misma `key=lambda item: get_album_order(item[0])` en
     `get_missing()` y `get_duplicates()` (`sorted(by_country.items())`) para
     que Faltantes/Repetidas listen los países en el mismo orden que el Álbum.
   - Reordenar `/api/stickers/search` por `album_order` — requiere mover el
     ordenamiento a Python (post-fetch, pre-paginación) o agregar columna a
     `master_stickers`. Se recomienda evaluarlo aparte si el usuario lo pide
     explícitamente.

### Nada de esto toca:

- `master_stickers.id` / `code` (no se re-siembra la tabla).
- `user_stickers` (no se modifica su esquema ni sus filas).
- `status.py` / lógica de colección (paste/unpaste/increment/decrement/mark-missing).
- `/api/nearby` (no usa `countries.json` ni el orden de álbum).
- Rutas, endpoints, modelos.

## 8. Riesgos

- **Bajo, en general** — el cambio es aditivo (un campo JSON nuevo) +
  reemplazar una clave de `sorted()` por otra. No hay migración de esquema ni
  de datos en SQLite.
- **Riesgo de typo/omisión en `countries.json`**: si a una de las 48
  selecciones le falta `album_order` o queda duplicado dentro de un grupo, el
  default (`99`) evita un crash, pero el orden visual de ese grupo quedaría
  mal (esa selección al final). Mitigación: comando de verificación en la
  sección 9 que valida 1-4 únicos por grupo.
- **FWC / `special`**: solo tiene 1 elemento (`FWC`), así que `sorted()` con
  cualquier clave es un no-op. Sin riesgo.
- **Frontend**: cero cambios de código, pero como el *orden* de los arrays
  cambia, cualquier `key={...}` en `.map()` debe seguir siendo estable por
  `country_code`/`id` (ya lo es en `Album.jsx` y `Dashboard.jsx` — no usan el
  índice del array como `key`). Verificado: `key={country.country_code}` y
  `key={sticker.id}`.
- **Buscar / Faltantes / Repetidas**: si se deja el fix mínimo (solo
  `get_album()`), estas pantallas siguen exactamente igual que hoy — cero
  riesgo de romperlas. Si más adelante se decide extender el orden a
  Faltantes/Repetidas (Fase 2 opcional), el riesgo sigue siendo bajo porque es
  la misma técnica (cambiar la `key` de un `sorted()` ya existente).

## 9. Archivos a tocar (fix mínimo)

1. `data/countries.json` — agregar `album_order` (1-4) a las 48 selecciones.
2. `backend/app/countries.py` — agregar `get_album_order()`.
3. `backend/app/routes/reports.py` — usar `get_album_order` como `key` en el
   `sorted()` de `countries.items()` dentro de `get_album()`.

Ningún otro archivo (CSV, modelos, schemas, rutas de colección, frontend)
necesita cambios para resolver el pedido del Álbum/Dashboard.

## 10. Comandos de verificación (a correr después de implementar)

### a) Validar `album_order` en `countries.json` (1-4 únicos por grupo, 48 entradas)

```bash
node -e "
const data = require('./data/countries.json');
const byGroup = {};
for (const c of data) {
  if (!c.group) continue; // omite FWC
  (byGroup[c.group] ||= []).push([c.album_order, c.fifa_code]);
}
let ok = true;
for (const g of Object.keys(byGroup).sort()) {
  const orders = byGroup[g].map(([o]) => o).sort();
  const expected = JSON.stringify([1,2,3,4]);
  if (JSON.stringify(orders) !== expected) {
    ok = false;
    console.log('GRUPO', g, 'MAL:', byGroup[g]);
  }
}
console.log(ok ? 'OK: 48 selecciones, album_order 1-4 unico por grupo' : 'HAY ERRORES');
"
```

### b) Confirmar el nuevo orden de `/api/reports/album` contra la fuente de verdad

```bash
curl -s "http://localhost:5173/api/reports/album" -o album.tmp.json && node -e "
const data = require('./album.tmp.json');
const expected = {
  A: ['MEX','RSA','KOR','CZE'],
  B: ['CAN','BIH','QAT','SUI'],
  C: ['BRA','MAR','HAI','SCO'],
  D: ['USA','PAR','AUS','TUR'],
  E: ['GER','CUW','CIV','ECU'],
  F: ['NED','JAP','SWE','TUN'],
  G: ['BEL','EGY','IRN','NZL'],
  H: ['CPV','KSA','ESP','URU'],
  I: ['FRA','IRQ','NOR','SEN'],
  J: ['ARG','ALG','AUT','JOR'],
  K: ['POR','COD','UZB','COL'],
  L: ['ENG','CRO','PAN','GHA'],
};
let ok = true;
for (const g of data.groups) {
  const got = g.countries.map(c => c.country_code);
  const exp = expected[g.group];
  if (JSON.stringify(got) !== JSON.stringify(exp)) {
    ok = false;
    console.log('Grupo', g.group, 'esperado', exp, 'obtenido', got);
  }
}
console.log(ok ? 'OK: orden de album coincide con fuente de verdad' : 'HAY DIFERENCIAS');
" && rm album.tmp.json
```

### c) Confirmar que no se perdió ningún estado de colección (`user_stickers`)

Antes y después del cambio, debe dar el mismo resultado (mismo conteo y misma
suma de `quantity`/`is_pasted`):

```bash
cd backend && .venv/Scripts/python -c "
from app.database import SessionLocal
from app import models
db = SessionLocal()
print('user_stickers:', db.query(models.UserSticker).count())
print('pegadas:', db.query(models.UserSticker).filter(models.UserSticker.is_pasted==True).count())
print('master_stickers:', db.query(models.MasterSticker).count())
db.close()
"
```

### d) Confirmar que `master_stickers.id`/`code` no cambiaron (no se re-sembró)

```bash
cd backend && .venv/Scripts/python -c "
from app.database import SessionLocal
from app import models
db = SessionLocal()
rows = db.query(models.MasterSticker.id, models.MasterSticker.code).order_by(models.MasterSticker.id).limit(5).all()
for r in rows: print(r)
db.close()
"
```

### e) Smoke test de pantallas no afectadas (deben seguir igual)

```bash
curl -s "http://localhost:5173/api/reports/missing" | node -e "process.stdin.resume()" # 200 OK
curl -s "http://localhost:5173/api/reports/duplicates" -o /dev/null -w "%{http_code}\n"
curl -s "http://localhost:5173/api/stickers/search?q=ARG" -o /dev/null -w "%{http_code}\n"
curl -s "http://localhost:5173/api/nearby" -o /dev/null -w "%{http_code}\n"
```

### f) Build de frontend (debe seguir compilando igual, 0 archivos frontend tocados)

```bash
cd frontend && npm run build
```

---

## Resumen ejecutivo

- El "orden alfabético accidental" existe y está confirmado: `reports.py`
  ordena `countries.items()` con `sorted()` plano (alfabético por
  `country_code`) en `get_album()`, `get_missing()` y `get_duplicates()`; y
  `stickers.py` usa `order_by(country_code, number)` en `/search`.
- El orden de inserción de `countries.json`/CSV **casi** sirve (9/12 grupos),
  pero no para H, I, L — hace falta codificar el orden real explícitamente.
- Campo recomendado: **`album_order`** (1-4), agregado a las 48 selecciones en
  **`data/countries.json`**.
- Fix mínimo: 3 archivos (`countries.json`, `countries.py`,
  `routes/reports.py`), solo afecta `get_album()` → corrige Álbum y Dashboard.
  Cero cambios en frontend, modelos, CSV, `user_stickers`, `master_stickers`,
  `/api/nearby`.
- Faltantes/Repetidas/Buscar quedan igual que hoy; extenderles el mismo orden
  es opcional y se puede hacer después con la misma técnica.
