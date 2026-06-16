# Reporte de corrección: JPN + Orden grupos H/I/L

**Fecha:** 2026-06-15  
**Basado en:** `BUG_AUDIT_GROUP_ORDER_JPN.md`  
**Estado:** IMPLEMENTADO Y VERIFICADO

---

## 1. Archivos modificados

| Archivo | Cambio |
|---|---|
| `data/countries.json` | `fifa_code` JAP→JPN, `flag_path` JAP.png→JPN.png; `album_order` de ESP, CPV, KSA (Grupo H), SEN, IRQ, NOR (Grupo I), GHA, PAN (Grupo L) |
| `data/stickers_master.csv` | 20 filas: `code` JAP1..JAP20→JPN1..JPN20, `country_code` JAP→JPN |
| `backend/stickercontrol.db` | UPDATE in-place en `master_stickers` (ids 485–504): `code` y `country_code` JAP→JPN |
| `frontend/public/flags/JPN.png` | Renombrado desde `JAP.png` (mismo contenido, nombre corregido) |

**Archivos NO modificados:** todo lo demás — rutas backend, lógica de colección, modelos, schemas, frontend JSX/JS/CSS, `seed_db.py`, `countries.py`, `reports.py`.

---

## 2. Backup creado

```
backend/stickercontrol.db.bak-jpn-groups-20260615-224446
```

Tamaño: 122 880 bytes (idéntico al original antes del cambio).  
Creado con `Copy-Item` antes de ejecutar cualquier SQL.

---

## 3. SQL ejecutado

```sql
-- Renombrar codes: JAP1..JAP20 → JPN1..JPN20
-- substr(code, 4) elimina el prefijo "JAP" (3 chars) y concatena "JPN"
UPDATE master_stickers
    SET code = 'JPN' || substr(code, 4)
    WHERE country_code = 'JAP';
-- Filas afectadas: 20

-- Renombrar country_code
UPDATE master_stickers
    SET country_code = 'JPN'
    WHERE country_code = 'JAP';
-- Filas afectadas: 20
```

No se ejecutó `seed_db.py`. Los `id` 485–504 se preservaron intactos.

---

## 4. Cambios en `data/countries.json`

### Bug A — Japón (fifa_code)

| Campo | Antes | Después |
|---|---|---|
| `fifa_code` | `"JAP"` | `"JPN"` |
| `flag_path` | `"/flags/JAP.png"` | `"/flags/JPN.png"` |
| `group` | `"F"` | `"F"` (sin cambio) |
| `album_order` | `2` | `2` (sin cambio) |

### Bug B — album_order grupos H, I, L

| `fifa_code` | Grupo | `album_order` antes | `album_order` después |
|---|---|---|---|
| ESP | H | 3 | **1** |
| CPV | H | 1 | **2** |
| KSA | H | 2 | **3** |
| URU | H | 4 | 4 (sin cambio) |
| FRA | I | 1 | 1 (sin cambio) |
| SEN | I | 4 | **2** |
| IRQ | I | 2 | **3** |
| NOR | I | 3 | **4** |
| ENG | L | 1 | 1 (sin cambio) |
| CRO | L | 2 | 2 (sin cambio) |
| GHA | L | 4 | **3** |
| PAN | L | 3 | **4** |

---

## 5. Validaciones realizadas

### countries.json — validación Python

| Check | Resultado |
|---|---|
| JAP ausente en todos los campos | ✅ `False` |
| JPN presente con `fifa_code`, `flag_path`, `group`, `album_order` correctos | ✅ `True` |
| `album_order` 1-4 únicos por grupo — los 12 grupos | ✅ todos OK |
| Grupo H = ESP, CPV, KSA, URU | ✅ CORRECTO |
| Grupo I = FRA, SEN, IRQ, NOR | ✅ CORRECTO |
| Grupo L = ENG, CRO, GHA, PAN | ✅ CORRECTO |
| Grupo F = NED, JPN, SWE, TUN | ✅ CORRECTO |

### backend — módulo `countries.py`

| Check | Resultado |
|---|---|
| `load_countries().get('JAP')` | ✅ `None` |
| `load_countries().get('JPN')` existe | ✅ `True` |
| `get_flag_path('JAP')` | ✅ `None` |
| `get_flag_path('JPN')` | ✅ `/flags/JPN.png` |
| `get_album_order` ordena Grupo H correctamente | ✅ `ESP, CPV, KSA, URU` |
| `get_album_order` ordena Grupo I correctamente | ✅ `FRA, SEN, IRQ, NOR` |
| `get_album_order` ordena Grupo L correctamente | ✅ `ENG, CRO, GHA, PAN` |

### DB (`master_stickers`)

| Check | Resultado |
|---|---|
| `code LIKE 'JAP%'` | ✅ 0 filas |
| `country_code = 'JAP'` | ✅ 0 filas |
| `code LIKE 'JPN%'` | ✅ 20 filas |
| `country_code = 'JPN'` | ✅ 20 filas |
| Rango de `id` para JPN | ✅ 485–504 (preservados) |
| Rango de `code` para JPN | ✅ JPN1–JPN9 (mín/máx lexicográfico) |
| `master_stickers` total | ✅ 980 |
| `user_stickers` total | ✅ 36 (sin cambios) |
| `user_stickers` pegadas | ✅ 28 (sin cambios) |

### CSV (`stickers_master.csv`)

| Check | Resultado |
|---|---|
| Filas que empiezan con `JAP` | ✅ 0 |
| Filas que empiezan con `JPN` | ✅ 20 |

### Flag file

| Check | Resultado |
|---|---|
| `frontend/public/flags/JAP.png` existe | ✅ No (eliminado) |
| `frontend/public/flags/JPN.png` existe | ✅ Sí (549 bytes) |

### Build de frontend

```
> vite build
✓ 53 modules transformed.
dist/index.html                  0.60 kB │ gzip:  0.35 kB
dist/assets/index-BWPvlMnO.css  15.85 kB │ gzip:  3.86 kB
dist/assets/index-DvrnGsJW.js  198.50 kB │ gzip: 62.30 kB
✓ built in 2.00s
```

**Resultado: BUILD OK** — sin errores ni warnings.

### Smoke test backend

Los endpoints protegidos devuelven `401 "No autenticado"` — comportamiento correcto
desde Fase 2A (Google Login). La lógica de datos se verificó directamente desde
el módulo Python (`countries.py`, `sqlite3`), que es la capa que `reports.py`
llama internamente.

---

## 6. Confirmación explícita de lo que NO se tocó

| Componente | Estado |
|---|---|
| Google Login / auth (`auth.py`, `/api/auth/*`, `AuthContext`, `PrivateRoute`, `Login.jsx`) | **NO TOCADO** |
| Sesiones / cookies (`SessionMiddleware`) | **NO TOCADO** |
| Responsive / mobile (Layout, Album, Missing, Duplicates, Dashboard) | **NO TOCADO** |
| Diseño visual (colores, badges, ProgressRing, StickerDetailModal, Tailwind config) | **NO TOCADO** |
| Rutas frontend (`App.jsx`, `vite.config.js`, `main.jsx`) | **NO TOCADO** |
| nginx / VPS / systemd / producción | **NO TOCADO** |
| `backend/app/routes/reports.py` | **NO TOCADO** |
| `backend/app/countries.py` | **NO TOCADO** |
| `backend/app/routes/nearby.py` | **NO TOCADO** |
| `backend/app/models.py` / `schemas.py` / `crud.py` | **NO TOCADO** |
| `backend/app/status.py` | **NO TOCADO** |
| `seed_db.py` | **NO EJECUTADO** |
| `user_stickers` (esquema y filas) | **NO TOCADO** |

---

## 7. Estado de la DB

| Métrica | Antes | Después |
|---|---|---|
| `master_stickers` total | 980 | 980 |
| Japón `country_code` | `JAP` | `JPN` |
| Japón codes | `JAP1..JAP20` | `JPN1..JPN20` |
| Japón `id` range | 485–504 | 485–504 (preservados) |
| `user_stickers` total | 36 | 36 |
| `user_stickers` pegadas | 28 | 28 |
| Filas JAP con `user_stickers` | 0 | 0 |

---

## 8. Nota para producción (VPS)

Antes de aplicar en el VPS:

1. Hacer backup de la DB productiva.
2. Ejecutar los mismos 2 UPDATE in-place en `stickercontrol.db` del servidor.
3. Copiar los archivos actualizados: `data/countries.json`, `data/stickers_master.csv`, `frontend/public/flags/JPN.png` (y eliminar `JAP.png`).
4. Reiniciar el backend (`systemctl restart stickercontrol-backend`) para invalidar el `lru_cache` de `load_countries()`.
5. Hacer `npm run build` y copiar `frontend/dist/` al directorio servido por nginx.

No se necesitan cambios en nginx ni en ninguna variable de entorno.
