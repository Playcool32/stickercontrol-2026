"""
Autenticacion (Fase 2A) - login con Google + sesion por cookie.

get_current_user_id() lee el user_id guardado en la sesion (cookie firmada
por SessionMiddleware, ver main.py). Si no hay sesion valida, devuelve 401.
Todas las rutas existentes ya dependen de esta funcion
(Depends(get_current_user_id)), por lo que no necesitan cambios.
"""

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from . import models

SESSION_USER_KEY = "user_id"


def get_current_user_id(request: Request) -> int:
    user_id = request.session.get(SESSION_USER_KEY)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return user_id


def get_or_create_user_from_google(
    db: Session,
    *,
    google_id: str,
    email: str,
    name: str,
    avatar: str | None,
) -> models.User:
    """Busca un usuario por google_id (y por email como respaldo) o crea uno
    nuevo. Un usuario nuevo arranca sin filas en user_stickers (album
    vacio)."""

    user = db.query(models.User).filter(models.User.google_id == google_id).first()
    if user is None:
        user = db.query(models.User).filter(models.User.email == email).first()

    if user is None:
        user = models.User(google_id=google_id, email=email, name=name, avatar=avatar)
        db.add(user)
    else:
        user.google_id = google_id
        user.email = email
        user.name = name
        user.avatar = avatar

    db.commit()
    db.refresh(user)
    return user
