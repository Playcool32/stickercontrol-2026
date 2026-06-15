"""
Login con Google + sesion (Fase 2A).

POST /api/auth/google: recibe el ID token (credential) entregado por Google
Identity Services en el frontend, lo valida contra GOOGLE_CLIENT_ID y crea/
actualiza el usuario y la sesion.
GET /api/auth/me: usuario autenticado actual (401 si no hay sesion).
POST /api/auth/logout: borra la sesion.
"""

import os

from fastapi import APIRouter, Depends, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy.orm import Session

from .. import models
from ..auth import SESSION_USER_KEY, get_current_user_id, get_or_create_user_from_google
from ..database import get_db
from ..schemas import GoogleLoginRequest, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


def _to_user_out(user: models.User) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name, avatar=user.avatar)


@router.post("/google", response_model=UserOut)
def login_google(
    payload: GoogleLoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID no configurado")

    try:
        idinfo = google_id_token.verify_oauth2_token(
            payload.credential, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Credential de Google invalida")

    user = get_or_create_user_from_google(
        db,
        google_id=idinfo["sub"],
        email=idinfo["email"],
        name=idinfo.get("name") or idinfo["email"],
        avatar=idinfo.get("picture"),
    )

    request.session[SESSION_USER_KEY] = user.id
    return _to_user_out(user)


@router.get("/me", response_model=UserOut)
def get_me(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="No autenticado")
    return _to_user_out(user)


@router.post("/logout")
def logout(request: Request):
    request.session.pop(SESSION_USER_KEY, None)
    return {"ok": True}
