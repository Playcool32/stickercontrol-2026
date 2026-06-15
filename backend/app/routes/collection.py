from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..crud import get_or_create_user_sticker, to_sticker_out
from ..database import get_db
from ..schemas import NotesUpdate, StickerOut

router = APIRouter(prefix="/api/collection", tags=["collection"])


def _get_master_sticker(db: Session, sticker_id: int) -> models.MasterSticker:
    sticker = db.get(models.MasterSticker, sticker_id)
    if sticker is None:
        raise HTTPException(status_code=404, detail="Sticker no encontrado")
    return sticker


def _respond(db: Session, sticker: models.MasterSticker, entry: models.UserSticker) -> StickerOut:
    db.commit()
    db.refresh(entry)
    return to_sticker_out(sticker, entry)


@router.post("/{sticker_id}/paste", response_model=StickerOut)
def paste_sticker(
    sticker_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.is_pasted = True
    return _respond(db, sticker, entry)


@router.post("/{sticker_id}/unpaste", response_model=StickerOut)
def unpaste_sticker(
    sticker_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.is_pasted = False
    return _respond(db, sticker, entry)


@router.post("/{sticker_id}/increment", response_model=StickerOut)
def increment_sticker(
    sticker_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.quantity += 1
    return _respond(db, sticker, entry)


@router.post("/{sticker_id}/decrement", response_model=StickerOut)
def decrement_sticker(
    sticker_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.quantity = max(entry.quantity - 1, 0)
    return _respond(db, sticker, entry)


@router.post("/{sticker_id}/mark-missing", response_model=StickerOut)
def mark_missing(
    sticker_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.quantity = 0
    entry.is_pasted = False
    return _respond(db, sticker, entry)


@router.patch("/{sticker_id}/notes", response_model=StickerOut)
def update_notes(
    sticker_id: int,
    payload: NotesUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    sticker = _get_master_sticker(db, sticker_id)
    entry = get_or_create_user_sticker(db, user_id, sticker_id)
    entry.notes = payload.notes
    return _respond(db, sticker, entry)
