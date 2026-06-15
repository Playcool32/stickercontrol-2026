from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user_id
from ..database import get_db
from ..geo import round_coord
from ..schemas import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _to_profile_out(user: models.User) -> ProfileOut:
    return ProfileOut(
        id=user.id,
        email=user.email,
        name=user.name,
        display_name=user.display_name,
        city=user.city,
        latitude=user.latitude,
        longitude=user.longitude,
        contact_email=user.contact_email,
        contact_whatsapp=user.contact_whatsapp,
        is_public=user.is_public,
    )


@router.get("", response_model=ProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = db.get(models.User, user_id)
    return _to_profile_out(user)


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    user = db.get(models.User, user_id)
    data = payload.model_dump(exclude_unset=True)

    if data.get("latitude") is not None:
        data["latitude"] = round_coord(data["latitude"])
    if data.get("longitude") is not None:
        data["longitude"] = round_coord(data["longitude"])

    for key, value in data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return _to_profile_out(user)
