"""
Fase 2B: link publico de solo lectura.

Endpoints autenticados (requieren sesion):
  POST /api/share/generate   → crea o devuelve el share_token del usuario
  GET  /api/share/token      → devuelve el share_token existente (None si no tiene)

Endpoints publicos (sin sesion, sin cookie):
  GET /api/public/{token}             → nombre del dueno del album
  GET /api/public/{token}/album       → AlbumResponse (notes suprimidas)
  GET /api/public/{token}/missing     → MissingResponse
  GET /api/public/{token}/duplicates  → DuplicatesResponse
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..countries import get_album_order, get_flag_path
from ..crud import get_user_sticker_map, to_sticker_out
from ..database import get_db
from ..schemas import (
    AlbumCountry,
    AlbumGroup,
    AlbumResponse,
    CountrySummary,
    DuplicateCountry,
    DuplicateItem,
    DuplicatesResponse,
    MissingCountry,
    MissingResponse,
    PublicOwnerResponse,
    ShareTokenResponse,
    StickerOut,
)
from ..status import FALTANTE
from .reports import _all_stickers_with_status, _country_sort_key, _format_number

router = APIRouter(tags=["share"])


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _get_user_by_token(token: str, db: Session) -> models.User:
    user = db.query(models.User).filter(models.User.share_token == token).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Álbum no encontrado")
    return user


def _build_public_country(country_code: str, data: dict) -> AlbumCountry:
    """Igual que build_country de reports.py pero suprime notes de cada sticker."""
    stickers_list: list[StickerOut] = [
        s.model_copy(update={"notes": None}) for s in data["stickers"]
    ]
    total = len(stickers_list)
    pegadas = sum(1 for st in stickers_list if st.is_pasted)
    faltantes = sum(1 for st in stickers_list if st.status == FALTANTE)
    repetidas = sum(st.repetidas for st in stickers_list)
    porcentaje = round((pegadas / total * 100), 1) if total else 0.0
    return AlbumCountry(
        country_code=country_code,
        country_name=data["country_name"],
        group=data["group"],
        flag=get_flag_path(country_code),
        stickers=stickers_list,
        summary=CountrySummary(
            total=total,
            pegadas=pegadas,
            faltantes=faltantes,
            repetidas=repetidas,
            porcentaje=porcentaje,
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints autenticados
# ---------------------------------------------------------------------------

@router.post("/api/share/generate", response_model=ShareTokenResponse)
def generate_share_token(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Genera el share_token del usuario si no existe; si ya existe lo devuelve."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user.share_token is None:
        user.share_token = secrets.token_urlsafe(16)
        db.commit()
        db.refresh(user)
    return ShareTokenResponse(token=user.share_token)


@router.get("/api/share/token", response_model=ShareTokenResponse)
def get_share_token(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    """Devuelve el share_token actual del usuario (None si todavia no genero link)."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    return ShareTokenResponse(token=user.share_token)


# ---------------------------------------------------------------------------
# Endpoints publicos (sin autenticacion)
# ---------------------------------------------------------------------------

@router.get("/api/public/{token}", response_model=PublicOwnerResponse)
def get_public_owner(token: str, db: Session = Depends(get_db)):
    user = _get_user_by_token(token, db)
    return PublicOwnerResponse(owner_name=user.name)


@router.get("/api/public/{token}/album", response_model=AlbumResponse)
def get_public_album(token: str, db: Session = Depends(get_db)):
    user = _get_user_by_token(token, db)

    groups: dict[str, dict[str, dict]] = {}
    special: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user.id):
        bucket = special if not sticker.group else groups.setdefault(sticker.group, {})
        country = bucket.setdefault(
            sticker.country_code,
            {"country_name": sticker.country_name, "group": sticker.group, "stickers": []},
        )
        country["stickers"].append(out)

    group_results = [
        AlbumGroup(
            group=group_code,
            countries=[
                _build_public_country(cc, data)
                for cc, data in sorted(countries.items(), key=lambda item: get_album_order(item[0]))
            ],
        )
        for group_code, countries in sorted(groups.items())
    ]
    special_results = [_build_public_country(cc, data) for cc, data in sorted(special.items())]
    return AlbumResponse(groups=group_results, special=special_results)


@router.get("/api/public/{token}/missing", response_model=MissingResponse)
def get_public_missing(token: str, db: Session = Depends(get_db)):
    user = _get_user_by_token(token, db)
    by_country: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user.id):
        if out.status == FALTANTE:
            bucket = by_country.setdefault(
                sticker.country_code,
                {"country_name": sticker.country_name, "group": sticker.group, "numbers": []},
            )
            bucket["numbers"].append(sticker.number)

    by_country_list = []
    lines = ["FALTANTES:"]
    for country_code, data in sorted(
        by_country.items(), key=lambda item: _country_sort_key(item[0], item[1]["group"])
    ):
        numbers = sorted(data["numbers"])
        by_country_list.append(
            MissingCountry(
                country_code=country_code,
                country_name=data["country_name"],
                numbers=numbers,
            )
        )
        lines.append(f"{country_code}: " + ", ".join(_format_number(n) for n in numbers))

    text = "\n".join(lines) if by_country_list else "FALTANTES:\n(sin faltantes)"
    return MissingResponse(by_country=by_country_list, text=text)


@router.get("/api/public/{token}/duplicates", response_model=DuplicatesResponse)
def get_public_duplicates(token: str, db: Session = Depends(get_db)):
    user = _get_user_by_token(token, db)
    by_country: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user.id):
        if out.repetidas > 0:
            bucket = by_country.setdefault(
                sticker.country_code,
                {"country_name": sticker.country_name, "group": sticker.group, "items": []},
            )
            bucket["items"].append((sticker.number, out.repetidas))

    by_country_list = []
    lines = ["REPETIDAS:"]
    for country_code, data in sorted(
        by_country.items(), key=lambda item: _country_sort_key(item[0], item[1]["group"])
    ):
        items = sorted(data["items"])
        by_country_list.append(
            DuplicateCountry(
                country_code=country_code,
                country_name=data["country_name"],
                items=[DuplicateItem(number=n, quantity=q) for n, q in items],
            )
        )
        parts = [f"{_format_number(n)}(x{q})" if q > 1 else _format_number(n) for n, q in items]
        lines.append(f"{country_code}: " + ", ".join(parts))

    text = "\n".join(lines) if by_country_list else "REPETIDAS:\n(sin repetidas)"
    return DuplicatesResponse(by_country=by_country_list, text=text)
