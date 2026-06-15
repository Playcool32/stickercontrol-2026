from sqlalchemy.orm import Session

from . import models
from .schemas import StickerOut
from .status import FALTANTE, compute_repetidas, compute_status


def to_sticker_out(sticker: models.MasterSticker, entry: models.UserSticker | None) -> StickerOut:
    quantity = entry.quantity if entry else 0
    is_pasted = entry.is_pasted if entry else False
    notes = entry.notes if entry else None

    return StickerOut(
        id=sticker.id,
        code=sticker.code,
        group=sticker.group,
        country_code=sticker.country_code,
        country_name=sticker.country_name,
        number=sticker.number,
        player_name_or_detail=sticker.player_name_or_detail,
        type=sticker.type,
        quantity=quantity,
        is_pasted=is_pasted,
        notes=notes,
        status=compute_status(quantity, is_pasted),
        repetidas=compute_repetidas(quantity, is_pasted),
    )


def get_user_sticker_map(
    db: Session, user_id: int, sticker_ids: list[int]
) -> dict[int, models.UserSticker]:
    if not sticker_ids:
        return {}

    entries = (
        db.query(models.UserSticker)
        .filter(
            models.UserSticker.user_id == user_id,
            models.UserSticker.sticker_id.in_(sticker_ids),
        )
        .all()
    )
    return {entry.sticker_id: entry for entry in entries}


def get_missing_and_duplicate_codes(db: Session, user_id: int) -> tuple[set[str], set[str]]:
    """Codigos FALTANTE y codigos con repetidas>0 de un usuario, usado por /api/nearby."""
    stickers = db.query(models.MasterSticker).all()
    entry_map = get_user_sticker_map(db, user_id, [s.id for s in stickers])

    missing: set[str] = set()
    duplicates: set[str] = set()
    for sticker in stickers:
        entry = entry_map.get(sticker.id)
        quantity = entry.quantity if entry else 0
        is_pasted = entry.is_pasted if entry else False

        if compute_status(quantity, is_pasted) == FALTANTE:
            missing.add(sticker.code)
        if compute_repetidas(quantity, is_pasted) > 0:
            duplicates.add(sticker.code)

    return missing, duplicates


def get_or_create_user_sticker(db: Session, user_id: int, sticker_id: int) -> models.UserSticker:
    entry = (
        db.query(models.UserSticker)
        .filter(
            models.UserSticker.user_id == user_id,
            models.UserSticker.sticker_id == sticker_id,
        )
        .first()
    )
    if entry is None:
        entry = models.UserSticker(
            user_id=user_id, sticker_id=sticker_id, quantity=0, is_pasted=False
        )
        db.add(entry)
        db.flush()
    return entry
