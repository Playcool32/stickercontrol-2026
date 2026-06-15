from fastapi import APIRouter, Depends
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
    StickerOut,
)
from ..status import FALTANTE

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _all_stickers_with_status(db: Session, user_id: int):
    stickers = (
        db.query(models.MasterSticker)
        .order_by(models.MasterSticker.country_code, models.MasterSticker.number)
        .all()
    )
    entry_map = get_user_sticker_map(db, user_id, [s.id for s in stickers])
    return [(s, to_sticker_out(s, entry_map.get(s.id))) for s in stickers]


def _country_sort_key(country_code: str, group: str | None) -> tuple:
    """Especiales del Mundial (group=None, ej. FWC) primero; despues
    grupos A-L en orden alfabetico y, dentro de cada grupo, segun
    get_album_order (orden real del album/sorteo)."""
    if group is None:
        return (0, country_code)
    return (1, group, get_album_order(country_code))


@router.get("/album", response_model=AlbumResponse)
def get_album(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    groups: dict[str, dict[str, dict]] = {}
    special: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user_id):
        bucket = special if not sticker.group else groups.setdefault(sticker.group, {})
        country = bucket.setdefault(
            sticker.country_code,
            {"country_name": sticker.country_name, "group": sticker.group, "stickers": []},
        )
        country["stickers"].append(out)

    def build_country(country_code: str, data: dict) -> AlbumCountry:
        stickers_list: list[StickerOut] = data["stickers"]
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

    group_results = [
        AlbumGroup(
            group=group_code,
            countries=[
                build_country(cc, data)
                for cc, data in sorted(countries.items(), key=lambda item: get_album_order(item[0]))
            ],
        )
        for group_code, countries in sorted(groups.items())
    ]
    special_results = [build_country(cc, data) for cc, data in sorted(special.items())]

    return AlbumResponse(groups=group_results, special=special_results)


@router.get("/missing", response_model=MissingResponse)
def get_missing(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    by_country: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user_id):
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
            MissingCountry(country_code=country_code, country_name=data["country_name"], numbers=numbers)
        )
        lines.append(f"{country_code}: " + ", ".join(str(n) for n in numbers))

    text = "\n".join(lines) if by_country_list else "FALTANTES:\n(sin faltantes)"
    return MissingResponse(by_country=by_country_list, text=text)


@router.get("/duplicates", response_model=DuplicatesResponse)
def get_duplicates(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    by_country: dict[str, dict] = {}

    for sticker, out in _all_stickers_with_status(db, user_id):
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
        parts = [f"{n}(x{q})" if q > 1 else str(n) for n, q in items]
        lines.append(f"{country_code}: " + ", ".join(parts))

    text = "\n".join(lines) if by_country_list else "REPETIDAS:\n(sin repetidas)"
    return DuplicatesResponse(by_country=by_country_list, text=text)
