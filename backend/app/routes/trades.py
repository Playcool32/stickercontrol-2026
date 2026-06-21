"""
Intercambios (Fase 2D) - MVP de solo lectura: cruza mis faltantes/repetidas
contra las de otro usuario publico, igual que /api/nearby, pero para un
other_user_id puntual. Sin chat, sin solicitudes persistentes, sin historial.
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..crud import get_missing_and_duplicate_codes
from ..database import get_db
from ..schemas import TradeMatchResponse, TradeOtherUser

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/status")
def trades_status():
    return {"implemented": False, "phase": "futura - intercambios"}


@router.get("/with-user/{other_user_id}", response_model=TradeMatchResponse)
def get_trade_match(
    other_user_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    if other_user_id == user_id:
        raise HTTPException(status_code=400, detail="No se puede calcular un intercambio con uno mismo")

    other = db.get(models.User, other_user_id)
    if other is None or not other.is_public:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    me = db.get(models.User, user_id)

    my_missing, my_duplicates = get_missing_and_duplicate_codes(db, user_id)
    other_missing, other_duplicates = get_missing_and_duplicate_codes(db, other_user_id)

    i_can_give = sorted(my_duplicates & other_missing)
    i_can_receive = sorted(other_duplicates & my_missing)

    my_name = me.display_name or me.name
    give_text = ", ".join(i_can_give) if i_can_give else "(ninguna)"
    receive_text = ", ".join(i_can_receive) if i_can_receive else "(ninguna)"

    summary_text = (
        f"Hola, soy {my_name}.\n"
        "Calcule un posible intercambio en StickerControl 2026:\n"
        "\n"
        "Yo te puedo dar:\n"
        f"{give_text}\n"
        "\n"
        "Vos me podes dar:\n"
        f"{receive_text}\n"
        "\n"
        "¿Te interesa coordinar?"
    )

    whatsapp_url = None
    if other.contact_whatsapp:
        whatsapp_url = f"https://wa.me/{other.contact_whatsapp}?text={quote(summary_text, safe='')}"

    mailto_url = None
    if other.contact_email:
        subject = quote("Intercambio de figuritas StickerControl 2026", safe="")
        body = quote(summary_text, safe="")
        mailto_url = f"mailto:{other.contact_email}?subject={subject}&body={body}"

    return TradeMatchResponse(
        other_user=TradeOtherUser(
            id=other.id, display_name=other.display_name or other.name, city=other.city
        ),
        i_can_give=i_can_give,
        i_can_receive=i_can_receive,
        summary_text=summary_text,
        whatsapp_url=whatsapp_url,
        mailto_url=mailto_url,
    )
