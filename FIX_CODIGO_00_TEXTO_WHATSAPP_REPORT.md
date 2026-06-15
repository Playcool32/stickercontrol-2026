# Follow-up — código "00" en texto de WhatsApp/portapapeles (Faltantes/Repetidas)

Cambio puntual de backend, sin refactor. DB sin cambios, API sin cambios
estructurales (mismos endpoints, mismos campos, solo cambia el contenido de
`text`).

## 1. Causa raíz

`data.text` (usado por "Copiar para WhatsApp" en `Missing.jsx` y
`Duplicates.jsx`) se genera **en el backend**, a partir de `sticker.number`:

```python
lines.append(f"{country_code}: " + ", ".join(str(n) for n in numbers))         # missing
parts = [f"{n}(x{q})" if q > 1 else str(n) for n, q in items]                    # duplicates
```

Para el Logo Oficial Mundial 2026 (`code="00"`, `number=0`), `str(0) == "0"`,
por lo que el texto mostraba `0` en vez de `00`, aunque los badges en pantalla
(ya corregidos en el fix anterior) muestren `00` correctamente.

## 2. Cambio realizado

### `backend/app/routes/reports.py`

**Nueva función helper** (antes de `_country_sort_key`):

```python
def _format_number(number: int) -> str:
    """El Logo Oficial Mundial 2026 tiene number=0 pero code="00"; en los
    textos de faltantes/repetidas debe mostrarse como "00", no "0"."""
    return "00" if number == 0 else str(number)
```

**`get_missing`** — línea donde se arma cada línea de `text`:

```diff
-        lines.append(f"{country_code}: " + ", ".join(str(n) for n in numbers))
+        lines.append(f"{country_code}: " + ", ".join(_format_number(n) for n in numbers))
```

**`get_duplicates`** — línea donde se arman los `parts` de `text`:

```diff
-        parts = [f"{n}(x{q})" if q > 1 else str(n) for n, q in items]
+        parts = [f"{_format_number(n)}(x{q})" if q > 1 else _format_number(n) for n, q in items]
```

`number == 0` identifica sin ambigüedad a `code="00"` (único caso en todo el
catálogo, ver fix anterior), por lo que es equivalente a la regla pedida
(`sticker.code == "00" or sticker.number == 0`) sin necesitar acceder a
`sticker.code` en este punto.

## 3. Archivos modificados

- `backend/app/routes/reports.py` (1 función helper nueva + 2 líneas
  modificadas, dentro de `get_missing` y `get_duplicates`)

No se modificó:
- DB / esquema / datos.
- `schemas.py` (estructura de `MissingResponse`/`DuplicatesResponse` sin
  cambios — `by_country`, `numbers`, `items` siguen siendo enteros).
- Frontend: `Missing.jsx`/`Duplicates.jsx` ya mapeaban `number === 0 → "00"`
  en los badges (fix anterior) y `handleCopy` simplemente copia
  `data.text`, que ahora ya viene corregido desde el backend — no requieren
  cambios adicionales.

## 4. Build frontend

No se tocó el frontend, por lo que no se requiere rebuild. `dist/` queda con
el build del fix anterior (`index-AsaX4bFt.js`).

## 5. Smoke test backend

```
$ .venv/Scripts/python.exe -c "..."
```

a) Unit del helper y de la lógica de armado de línea:

```
missing line    -> FWC: 00, 1, 2, 3, 19
duplicates line -> FWC: 00(x2), 1, 19(x3)
OK
```

b) Import de la app completa (chequeo de sintaxis/wiring):

```
App importada OK, rutas: 20
```

c) Ejecución real de `get_missing(db, user_id=1)` y
`get_duplicates(db, user_id=1)` contra `backend/stickercontrol.db` (dataset
local actual, sin TestClient por no tener `httpx` instalado — se llamó la
función de la ruta directamente con una sesión real de SQLAlchemy):

```
MISSING text:
FALTANTES:
FWC: 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19
MEX: 5, 6, 7, ...
...

DUPLICATES text:
REPETIDAS:
FWC: 1
MEX: 1, 3(x2)
...
```

Ambas llamadas completaron **sin errores**. Como ya se documentó en el fix
anterior, en el dataset local `00` (id=985) tiene `quantity=0, is_pasted=1`
→ no es `FALTANTE` ni tiene `repetidas>0`, por lo que no aparece en ninguna
de las dos listas con los datos actuales — coherente con lo observado (`FWC`
arranca en `4` en Faltantes). La prueba (a) confirma con números simulados
(incluyendo `0`) que, cuando `00` sí aparezca, el texto mostrará `FWC: 00,
...` y `FWC: 00(xN), ...` en vez de `FWC: 0, ...`.

**Resultado: BACKEND SMOKE TEST OK** (sin errores).

## 6. Verificación de los puntos pedidos

| Punto | Estado |
|---|---|
| Texto de faltantes muestra `FWC: 00, ...` cuando `00` es faltante | ✅ verificado con números simulados (no reproducible con dataset local actual, ver §5) |
| Texto de repetidas muestra `FWC: 00(xN), ...` cuando corresponde | ✅ verificado con números simulados (idem) |
| DB sin cambios | ✅ no se tocó |
| API sin cambios estructurales | ✅ mismos endpoints/campos, solo cambia contenido de `text` |
| `id` / `code` / `number` sin cambios | ✅ no se tocó |
| Frontend sin cambios adicionales | ✅ no fue necesario |
| Build frontend | N/A (no se tocó frontend) |
| Backend smoke test | ✅ OK |

## 7. Resultado

Con este cambio, el Logo Oficial Mundial 2026 (`code="00"`) se muestra como
`00` de forma consistente en **badges** (fix anterior, frontend) y en
**texto copiado/WhatsApp** (este fix, backend). Queda cerrada la
inconsistencia documentada como follow-up en
`FIX_CODIGO_00_FALTANTES_REPETIDAS_REPORT.md`.
