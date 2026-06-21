# Implementación — Carga masiva por país (Fase 2C)

Auditoría previa: [`BULK_MARK_COUNTRY_AUDIT.md`](./BULK_MARK_COUNTRY_AUDIT.md) (riesgo bajo → se procede).

## 1. Archivos modificados

| Archivo | Cambio |
|---|---|
| `backend/app/schemas.py` | Nuevo schema `BulkMarkCountryResponse` (`country_code`, `marked`, `total`). |
| `backend/app/routes/collection.py` | Nuevo endpoint `POST /api/collection/bulk-mark-country/{country_code}`. |
| `frontend/src/api/client.js` | Nueva función `bulkMarkCountry(countryCode)`. |
| `frontend/src/pages/Album.jsx` | Botón "Marcar selección completa" en `CountryCard`, confirmación previa, feedback simple y refresh del álbum. |

No se tocó: `reports.py`, `share.py`, `auth.py`, `models.py`, `master_stickers`, ningún archivo de Login/Google, ni `Search.jsx`/`Missing.jsx`/`Duplicates.jsx`. Sin migración de DB.

### Backend — endpoint

```python
@router.post("/bulk-mark-country/{country_code}", response_model=BulkMarkCountryResponse)
def bulk_mark_country(country_code: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    stickers = db.query(models.MasterSticker).filter(
        models.MasterSticker.country_code == country_code.upper()
    ).all()
    if not stickers:
        raise HTTPException(status_code=404, detail="Pais no encontrado")
    for sticker in stickers:
        entry = get_or_create_user_sticker(db, user_id, sticker.id)
        entry.is_pasted = True
    db.commit()
    return BulkMarkCountryResponse(country_code=country_code.upper(), marked=len(stickers), total=len(stickers))
```

Un solo `db.commit()` al final → atómico. Nunca toca `quantity` ni `notes`. Mismo `get_or_create_user_sticker` que usan `paste`/`unpaste`/etc.

### Frontend — botón + confirmación

En `CountryCard`, junto al `ProgressRing`, se agregó un botón que llama `onBulkMark(country.country_code, summary.total)`. En `Album.jsx`, `handleBulkMark` muestra `window.confirm` con el texto pedido (usando el total real del país, no hardcodeado), y si se confirma llama al endpoint, refresca el álbum con `loadAlbum()` y muestra un mensaje de feedback (`"ARG: 5/5 marcadas como pegadas."`) arriba de la lista.

## 2. Resultado de build

```
> vite build
✓ 54 modules transformed.
dist/index.html                  0.60 kB
dist/assets/index-nKmjoN4p.css   16.36 kB
dist/assets/index-Caox1mYF.js   209.46 kB
✓ built in 2.28s
```

Backend: `python -c "import app.main"` y `python -m compileall app` → sin errores.

## 3. Resumen de validaciones

Smoke test ad-hoc con `TestClient` sobre una DB SQLite temporal aislada (2 usuarios, país ARG con 5 figuritas, una con `quantity=3` + `notes` previas), corrido y luego borrado:

| # | Validación | Resultado |
|---|---|---|
| 1 | Usuario A marca ARG completa | OK — endpoint 200, `{country_code: "ARG", marked: 5, total: 5}` |
| 2 | ARG queda 5/5 | OK — `summary.pegadas == summary.total == 5` |
| 3 | Usuario B no cambia | OK — álbum de B sigue en 0/5 pegadas |
| 4 | `quantity` > 1 se preserva | OK — ARG2 sigue con `quantity=3` |
| 5 | `notes` se preservan | OK — ARG2 conserva `"nota importante"` |
| 6 | Se puede desmarcar una figurita después | OK — `unpaste` sobre ARG1 devuelve `is_pasted=false` |
| 7 | Faltantes se recalculan | OK — ARG1 vuelve a aparecer en `/api/reports/missing` tras desmarcar |
| 8 | Repetidas se recalculan | OK — ARG2 (`quantity=3`, pegada) aparece en `/api/reports/duplicates` con `repetidas=3` |
| 9 | Share público refleja el estado nuevo | OK — `/api/public/{token}/album` muestra 4/5 pegadas tras desmarcar ARG1, y `notes` suprimidas |
| 10 | `npm run build` OK | OK — ver sección 2 |
| 11 | Backend smoke test OK | OK — 13/13 checks pasaron (incluye además el caso `país inexistente → 404`) |

Total: **13/13 checks OK**, sin fallos funcionales. (El único error encontrado durante la corrida fue un `PermissionError` de Windows al intentar borrar el archivo `.db` temporal después de que el test ya había terminado y reportado todo OK — no afecta el resultado, era limpieza de un proceso temporal que ya se descartó junto con el script.)

## 4. Commit recomendado (no se hizo push)

```
git add backend/app/schemas.py backend/app/routes/collection.py frontend/src/api/client.js frontend/src/pages/Album.jsx BULK_MARK_COUNTRY_AUDIT.md BULK_MARK_COUNTRY_IMPLEMENTATION_REPORT.md
git commit -m "feat: Fase 2C - carga masiva por pais (bulk-mark-country)"
```

No se ejecutó ningún `git add`/`git commit` automáticamente; queda a criterio del usuario confirmarlo.
