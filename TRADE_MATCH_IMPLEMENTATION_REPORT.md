# Implementación — Intercambios básicos desde Usuarios cerca (Fase 2D)

Auditoría previa: [`TRADE_MATCH_AUDIT.md`](./TRADE_MATCH_AUDIT.md) (riesgo bajo, caso 1 aprobado → se procede; caso 2 / share link queda fuera de alcance, documentado como Fase 2D.2).

## 1. Archivos modificados/creados

| Archivo | Cambio |
|---|---|
| `backend/app/schemas.py` | Nuevos schemas `TradeOtherUser` y `TradeMatchResponse`. |
| `backend/app/routes/trades.py` | Nuevo endpoint `GET /api/trades/with-user/{other_user_id}` (solo lectura). El placeholder `GET /api/trades/status` se mantiene intacto. |
| `frontend/src/api/client.js` | Nueva función `getTradeMatch(otherUserId)`. |
| `frontend/src/components/TradeResultPanel.jsx` (nuevo) | Tarjeta compartida "Vos podés darle / Te puede dar" + botón "Copiar resumen para WhatsApp", reutilizada por `Nearby.jsx` y `Trades.jsx` para no duplicar JSX. |
| `frontend/src/pages/Nearby.jsx` | Botón "Calcular intercambio" por tarjeta de usuario cercano; al confirmarse muestra `TradeResultPanel` inline. |
| `frontend/src/pages/Trades.jsx` | Deja de ser "Próximamente": lista los mismos usuarios públicos de `/api/nearby` con el mismo botón "Calcular intercambio". |

No se tocó: `models.py` (sin migración), `auth.py`, `share.py`, `reports.py`, `crud.py` (se reutilizó `get_missing_and_duplicate_codes` tal cual existía), `main.py` (el router de `trades` ya estaba incluido), nginx/VPS, lógica de `status.py`.

### Backend — endpoint

```python
@router.get("/with-user/{other_user_id}", response_model=TradeMatchResponse)
def get_trade_match(other_user_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if other_user_id == user_id:
        raise HTTPException(status_code=400, detail="No se puede calcular un intercambio con uno mismo")
    other = db.get(models.User, other_user_id)
    if other is None or not other.is_public:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    ...
    my_missing, my_duplicates = get_missing_and_duplicate_codes(db, user_id)
    other_missing, other_duplicates = get_missing_and_duplicate_codes(db, other_user_id)
    i_can_give = sorted(my_duplicates & other_missing)
    i_can_receive = sorted(other_duplicates & my_missing)
    ...
```

`other_user` en la respuesta solo expone `id`, `display_name`, `city` — sin email/whatsapp/coords planos. `whatsapp_url`/`mailto_url` se generan en el servidor con el mismo patrón ya usado en `/api/nearby/{id}/contact-message` (texto codificado con `quote`, URL armada del lado del backend).

### Frontend — botón + panel

`Nearby.jsx` y `Trades.jsx` comparten el mismo patrón: estado `trades` (map `user_id` → resultado) y `tradeErrors`, función `handleCalculateTrade(userId)` que llama `getTradeMatch` y guarda el resultado, y renderizan `<TradeResultPanel trade={...} />` debajo de la tarjeta del usuario. El botón "Copiar resumen para WhatsApp" usa `navigator.clipboard.writeText(trade.summary_text)`, mismo patrón que ya usa "Copiar mensaje" en `Nearby.jsx`.

## 2. Resultado de build

```
> vite build
✓ 55 modules transformed.
dist/index.html                  0.60 kB
dist/assets/index-B8D6eRAT.css   16.30 kB
dist/assets/index-Dv-u7WMb.js   212.15 kB
✓ built in 3.37s
```

Backend: `python -c "import app.main"` y `python -m compileall app` → sin errores.

## 3. Resumen de validaciones

Smoke test ad-hoc con `TestClient` sobre una DB SQLite temporal aislada (usuarios A y B públicos con colecciones cruzadas, C privado), corrido y luego borrado junto con el script:

| # | Validación | Resultado |
|---|---|---|
| 1 | A y B públicos | OK — fixtures con `is_public=True` |
| 2 | A calcula intercambio con B | OK — `GET /api/trades/with-user/{B.id}` → 200 |
| 3 | `i_can_give` correcto | OK — `["ARG10", "BRA4", "ESP7"]` (repetidas de A que a B le faltan) |
| 4 | `i_can_receive` correcto | OK — `["JPN12", "MEX3"]` (repetidas de B que a A le faltan) |
| 5 | Usuario no público → 404 | OK — probado contra C (`is_public=False`) |
| 6 | Usuario inexistente → 404 | OK — id `99999` |
| 7 | No se modifica `user_stickers` | OK — count y valores de todas las filas idénticos antes/después de la llamada |
| 8 | No se exponen `notes` | OK — el string `"nota secreta"` (puesto deliberadamente en `notes` de A y B) no aparece en ningún lado de la respuesta |
| 9 | Texto de WhatsApp se genera | OK — `summary_text` no vacío y contiene los códigos; `whatsapp_url` (`https://wa.me/...`) y `mailto_url` (`mailto:...`) generados porque B tiene `contact_whatsapp`/`contact_email` configurados |
| 10 | `npm run build` OK | OK — ver sección 2 |
| 11 | Backend compile/smoke test OK | OK — 13/13 checks pasaron (incluye además `other_user` sin campos sensibles y el caso extra "intercambio con uno mismo → 400") |

Total: **13/13 checks OK**. (Igual que en la entrega de Fase 2C, el único "error" en la corrida fue un `PermissionError` de Windows al borrar el `.db` temporal *después* de que todos los checks ya habían reportado OK — no afecta el resultado; se eliminó manualmente el archivo temporal a continuación.)

## 4. Commit recomendado (no se hizo push)

```
git add backend/app/routes/trades.py backend/app/schemas.py frontend/src/api/client.js frontend/src/pages/Nearby.jsx frontend/src/pages/Trades.jsx frontend/src/components/TradeResultPanel.jsx TRADE_MATCH_AUDIT.md TRADE_MATCH_IMPLEMENTATION_REPORT.md
git commit -m "feat: Fase 2D - intercambios basicos desde Usuarios cerca"
```

No se ejecutó ningún `git add`/`git commit`/`git push`; queda a criterio del usuario confirmarlo.
