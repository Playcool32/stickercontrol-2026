from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """Usuario autenticado con Google (Fase 2A). Cada usuario tiene su
    propia coleccion en user_stickers."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    google_id: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    name: Mapped[str] = mapped_column(String)
    avatar: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Perfil publico para "Usuarios cerca" (Fase 0.6). Vacios/None y
    # is_public=False por defecto: el usuario decide explicitamente que
    # mostrar.
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_whatsapp: Mapped[str | None] = mapped_column(String, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)

    stickers: Mapped[list["UserSticker"]] = relationship(back_populates="user")


class MasterSticker(Base):
    """
    Catalogo maestro de figuritas. Se llena via seed_db.py desde
    data/stickers_master.csv. La tabla arranca vacia: el dataset que se
    cargue hoy es de PRUEBA, pensado para reemplazarse por una importacion
    real desde Google Sheets (mismo patron que el import de paises).
    """

    __tablename__ = "master_stickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, unique=True, index=True)
    group: Mapped[str | None] = mapped_column(String, nullable=True)
    country_code: Mapped[str] = mapped_column(String, index=True)
    country_name: Mapped[str] = mapped_column(String)
    number: Mapped[int] = mapped_column(Integer)
    player_name_or_detail: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)

    user_entries: Mapped[list["UserSticker"]] = relationship(back_populates="sticker")


class UserSticker(Base):
    """Estado de coleccion de un usuario para una figurita del catalogo."""

    __tablename__ = "user_stickers"
    __table_args__ = (UniqueConstraint("user_id", "sticker_id", name="uq_user_sticker"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    sticker_id: Mapped[int] = mapped_column(ForeignKey("master_stickers.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    is_pasted: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(back_populates="stickers")
    sticker: Mapped["MasterSticker"] = relationship(back_populates="user_entries")
