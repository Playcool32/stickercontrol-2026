from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..crud import get_user_sticker_map, to_sticker_out
from ..database import get_db
from ..schemas import StickerSearchResponse

router = APIRouter(prefix="/api/stickers", tags=["stickers"])


@router.get("/search", response_model=StickerSearchResponse)
def search_stickers(
    q: str | None = Query(default=None, description="Busca en code, country_name, jugador/detalle o numero"),
    group: str | None = Query(default=None),
    country_code: str | None = Query(default=None),
    type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    query = db.query(models.MasterSticker)

    if group:
        query = query.filter(models.MasterSticker.group == group.upper())
    if country_code:
        query = query.filter(models.MasterSticker.country_code == country_code.upper())
    if type:
        query = query.filter(models.MasterSticker.type == type.lower())

    if q:
        q_like = f"%{q.strip()}%"
        conditions = [
            models.MasterSticker.code.ilike(q_like),
            models.MasterSticker.country_name.ilike(q_like),
            models.MasterSticker.player_name_or_detail.ilike(q_like),
        ]
        if q.strip().isdigit():
            conditions.append(models.MasterSticker.number == int(q.strip()))
        query = query.filter(or_(*conditions))

    total = query.count()
    stickers = (
        query.order_by(models.MasterSticker.country_code, models.MasterSticker.number)
        .offset(offset)
        .limit(limit)
        .all()
    )

    entry_map = get_user_sticker_map(db, user_id, [s.id for s in stickers])
    items = [to_sticker_out(sticker, entry_map.get(sticker.id)) for sticker in stickers]

    return StickerSearchResponse(total=total, items=items)
