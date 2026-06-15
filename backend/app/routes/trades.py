"""
Intercambios - modulo preparado, sin logica todavia (fase futura).

Cuando se implemente: parsear listas "ofrece"/"necesita" de otro
coleccionista, cruzarlas contra la coleccion del usuario (faltantes /
repetidas) y devolver el balance + texto para WhatsApp.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/trades", tags=["trades"])


@router.get("/status")
def trades_status():
    return {"implemented": False, "phase": "futura - intercambios"}
