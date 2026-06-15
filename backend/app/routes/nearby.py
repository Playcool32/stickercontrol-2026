"""
Usuarios cerca (Fase 0.6) - MVP minimo de intercambio sin chat interno.

`GET /api/nearby` cruza mis faltantes/repetidas con las de otros usuarios
publicos y devuelve coincidencias + distancia aproximada.
`GET /api/nearby/{user_id}/contact-message` genera el texto listo para
WhatsApp/email; el contacto real ocurre fuera de la app.
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..crud import get_missing_and_duplicate_codes
from ..database import get_db
from ..geo import haversine_km
from ..schemas import ContactMessageResponse, NearbyResponse, NearbyUser

router = APIRouter(prefix="/api/nearby", tags=["nearby"])


def _distance_km(me: models.User, other: models.User) -> float | None:
    if me.latitude is None or me.longitude is None:
        return None
    if other.latitude is None or other.longitude is None:
        return None
    return round(haversine_km(me.latitude, me.longitude, other.latitude, other.longitude), 1)


@router.get("", response_model=NearbyResponse)
def get_nearby(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    me = db.get(models.User, user_id)
    my_missing, my_duplicates = get_missing_and_duplicate_codes(db, user_id)

    others = (
        db.query(models.User)
        .filter(models.User.is_public == True, models.User.id != user_id)  # noqa: E712
        .all()
    )

    results = []
    for other in others:
        other_missing, other_duplicates = get_missing_and_duplicate_codes(db, other.id)

        stickers_i_need = sorted(my_missing & other_duplicates)
        stickers_they_need = sorted(other_missing & my_duplicates)

        results.append(
            NearbyUser(
                user_id=other.id,
                display_name=other.display_name or other.name,
                city=other.city,
                distance_km=_distance_km(me, other),
                stickers_i_need_that_user_has=stickers_i_need,
                stickers_user_needs_that_i_have=stickers_they_need,
                match_count=len(stickers_i_need) + len(stickers_they_need),
                has_email=bool(other.contact_email),
                has_whatsapp=bool(other.contact_whatsapp),
            )
        )

    results.sort(
        key=lambda r: (
            -r.match_count,
            r.distance_km if r.distance_km is not None else float("inf"),
        )
    )

    return NearbyResponse(users=results)


@router.get("/{other_user_id}/contact-message", response_model=ContactMessageResponse)
def get_contact_message(
    other_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    me = db.get(models.User, user_id)
    other = db.get(models.User, other_user_id)
    if other is None or not other.is_public:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    my_missing, my_duplicates = get_missing_and_duplicate_codes(db, user_id)
    other_missing, other_duplicates = get_missing_and_duplicate_codes(db, other_user_id)

    stickers_i_need = sorted(my_missing & other_duplicates)
    stickers_they_need = sorted(other_missing & my_duplicates)

    my_name = me.display_name or me.name
    i_need_text = ", ".join(stickers_i_need) if stickers_i_need else "(ninguna)"
    they_need_text = ", ".join(stickers_they_need) if stickers_they_need else "(ninguna)"

    text = (
        f"Hola, soy {my_name}.\n"
        "Vi en StickerControl 2026 que estamos cerca y tenemos figuritas para intercambiar.\n"
        "\n"
        "A mi me interesan:\n"
        f"{i_need_text}\n"
        "\n"
        "Yo tengo repetidas que quizas te sirven:\n"
        f"{they_need_text}\n"
        "\n"
        "¿Te interesa coordinar?"
    )

    whatsapp_url = None
    if other.contact_whatsapp:
        whatsapp_url = f"https://wa.me/{other.contact_whatsapp}?text={quote(text, safe='')}"

    mailto_url = None
    if other.contact_email:
        subject = quote("Intercambio de figuritas StickerControl 2026", safe="")
        body = quote(text, safe="")
        mailto_url = f"mailto:{other.contact_email}?subject={subject}&body={body}"

    return ContactMessageResponse(text=text, whatsapp_url=whatsapp_url, mailto_url=mailto_url)
