# Implementación: orden real del Álbum (grupos y selecciones)

Basado en `GROUP_ORDER_AUDIT.md`. Alcance controlado: solo lo descrito ahí
(fix mínimo + orden de Especiales primero).

## 1. Cambios implementados

### `data/countries.json`
- Agregado el campo `"album_order"` a las 49 entradas:
  - Las 48 selecciones reciben un entero `1-4` (posición real dentro de su
    grupo, según la fuente de verdad).
  - `FWC` recibe `"album_order": null` (no participa de este orden).
- Generado con un script Node de una sola pasada (mapeo grupo→[códigos] →
  `album_order`), preservando el formato JSON (2 espacios, mismo orden de
  entradas/array).

### `backend/app/countries.py`
- Nueva función:

  ```python
  def get_album_order(fifa_code: str) -> int:
      """Posicion (1-4) de la seleccion dentro de su grupo, segun el orden real
      del album/sorteo. Si falta el dato (o es FWC/especiales), devuelve un
      valor alto para que quede al final sin romper el orden."""
      country = load_countries().get(fifa_code)
      order = country.get("album_order") if country else None
      return order if order is not None else 99
  ```

  Reutiliza el loader cacheado existente (`load_countries()`), igual que
  `get_flag_path`.

### `backend/app/routes/reports.py`
- Import: `from ..countries import get_album_order, get_flag_path`.
- Nuevo helper:

  ```python
  def _country_sort_key(country_code: str, group: str | None) -> tuple:
      """Especiales del Mundial (group=None, ej. FWC) primero; despues
      grupos A-L en orden alfabetico y, dentro de cada grupo, segun
      get_album_order (orden real del album/sorteo)."""
      if group is None:
          return (0, country_code)
      return (1, group, get_album_order(country_code))
  ```

- **`get_album()`**: el `sorted(countries.items())` dentro de cada grupo ahora
  usa `key=lambda item: get_album_order(item[0])`. El orden de los grupos
  (A-L, `sorted(groups.items())`) y de `special` (`sorted(special.items())`,
  solo `FWC`) no cambió — ya eran correctos.
- **`get_missing()`** y **`get_duplicates()`**: el bucket `by_country` ahora
  guarda también `"group": sticker.group`, y el `sorted(by_country.items())`
  usa `key=lambda item: _country_sort_key(item[0], item[1]["group"])`. Esto
  ordena tanto `by_country` (JSON) como las líneas del `text` (WhatsApp): FWC
  primero, luego A-L con el orden real dentro de cada grupo.
- **`/api/stickers/search`**: sin cambios, sigue `order_by(country_code, number)`
  (alfabético), tal como se pidió.

### `frontend/src/pages/Album.jsx`
- Único cambio frontend, **estrictamente necesario**: la respuesta de
  `/api/reports/album` separa `groups` (A-L) y `special` (FWC) en dos arrays
  distintos; el frontend decidía el orden de renderizado. Se movió el bloque
  `<section>` de "Especiales del Mundial" (`album.special.map(...)`) para que
  se renderice **antes** del `album.groups.map(...)`, cumpliendo "Especiales
  primero, luego grupos A-L". No se tocó el componente `CountryCard`, los
  `key`, ni la lógica de selección/modal.

## 2. Archivos modificados

- `data/countries.json`
- `backend/app/countries.py`
- `backend/app/routes/reports.py`
- `frontend/src/pages/Album.jsx`

Ningún otro archivo (CSV, modelos, schemas, rutas de colección, `seed_db.py`,
`/api/nearby`, `/api/stickers/search`) fue tocado.

## 3. Verificaciones obligatorias — resultados

Backend reiniciado (hot-reload de `--reload` no detectó los cambios de forma
confiable dentro de la carpeta OneDrive, así que se reinició el proceso
uvicorn limpio en `:8000`).

| Verificación | Resultado |
|---|---|
| Total stickers | **980** ✅ |
| Selecciones (en `groups`) | **48** ✅ |
| Especiales (`special`, total stickers FWC) | **20** ✅ |
| `user_stickers` (conteo) | **32** (sin cambios) ✅ |
| `pegadas` (is_pasted=true) | **25** (sin cambios) ✅ |
| `master_stickers` (conteo + primeros ids/codes) | **980**, id 1-5 = `MEX1..MEX5` (sin re-seed) ✅ |
| Álbum Grupo A | `MEX, RSA, KOR, CZE` ✅ |
| Álbum Grupo H | `CPV, KSA, ESP, URU` ✅ |
| Álbum Grupo I | `FRA, IRQ, NOR, SEN` ✅ |
| Álbum Grupo L | `ENG, CRO, PAN, GHA` ✅ |
| Especiales (FWC) orden interno | `00, FWC1, FWC2, ..., FWC19` ✅ |
| Faltantes: FWC primero, luego A-L en orden real | `FWC, MEX, RSA, KOR, CZE, CAN, BIH, QAT, SUI, BRA, MAR, HAI, SCO, USA, PAR, AUS, TUR, GER, CUW, CIV, ECU, NED, JAP, SWE, TUN, BEL, EGY, IRN, NZL, CPV, KSA, ESP, URU, FRA, IRQ, NOR, SEN, ARG, ALG, AUT, JOR, POR, COD, UZB, COL, ENG, CRO, PAN, GHA` ✅ |
| Repetidas: FWC primero, luego A-L | `FWC, MEX, KOR, CZE, BRA, ARG` ✅ |
| Texto WhatsApp Faltantes/Repetidas | Empieza con `FWC: ...` y sigue con `MEX: ...` etc. ✅ |
| `/api/stickers/search?group=A` (orden sin cambios) | `CZE1, CZE2, ...` (alfabético, igual que antes) ✅ |
| `npm run build` | `✓ 51 modules transformed` / `✓ built in 2.20s` ✅ |
| Smoke `/api/reports/missing`, `/duplicates`, `/album`, `/nearby`, `/stickers/search` | todos `200` ✅ |

Todos los 12 grupos del Álbum verificados completos contra la fuente de
verdad:

```
A -> MEX, RSA, KOR, CZE
B -> CAN, BIH, QAT, SUI
C -> BRA, MAR, HAI, SCO
D -> USA, PAR, AUS, TUR
E -> GER, CUW, CIV, ECU
F -> NED, JAP, SWE, TUN
G -> BEL, EGY, IRN, NZL
H -> CPV, KSA, ESP, URU
I -> FRA, IRQ, NOR, SEN
J -> ARG, ALG, AUT, JOR
K -> POR, COD, UZB, COL
L -> ENG, CRO, PAN, GHA
special -> FWC
```

## 4. Restricciones respetadas

- **Lógica de colección** (`status.py`, paste/unpaste/increment/decrement/
  mark-missing): sin cambios.
- **`user_stickers`**: 32 filas, 25 pegadas — idénticos antes/después, no se
  tocó el esquema ni se re-sembró nada.
- **Códigos / IDs**: `master_stickers` sigue con 980 filas, mismos `id`/`code`
  (verificado `id 1 = MEX1` ... sin resiembra, `seed_db.py` no se ejecutó).
- **`/api/nearby`**: sin cambios, responde `200`.
- **`/api/stickers/search`**: sin cambios, orden alfabético como antes.

## 5. Riesgos detectados

- **Ninguno nuevo respecto a lo anticipado en la auditoría.** El cambio es
  aditivo (un campo JSON + dos claves de `sorted()` + un swap de bloques JSX).
- Único punto operativo a tener en cuenta: en este entorno (proyecto dentro de
  OneDrive), el `--reload` de uvicorn no siempre detecta cambios en todos los
  `.py` editados (detectó `countries.py` pero no `reports.py` en la misma
  tanda). Se solucionó reiniciando el proceso del backend manualmente. Si en
  el futuro se editan varios archivos backend seguidos, conviene reiniciar el
  servidor en vez de confiar en el autoreload.
- Dashboard no fue tocado: su tira de banderas (`data.groups.flatMap(g =>
  g.countries)`) hereda automáticamente el nuevo orden por grupo (no incluye
  FWC, sin cambios de comportamiento ahí).
