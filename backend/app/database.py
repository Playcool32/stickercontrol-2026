import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'stickercontrol.db'}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


USER_PROFILE_COLUMNS = {
    "display_name": "VARCHAR",
    "city": "VARCHAR",
    "latitude": "FLOAT",
    "longitude": "FLOAT",
    "contact_email": "VARCHAR",
    "contact_whatsapp": "VARCHAR",
    "is_public": "BOOLEAN DEFAULT 0",
}


def _ensure_user_profile_columns() -> None:
    """Agrega a `users` las columnas de perfil publico si faltan.

    No hay framework de migraciones (Alembic) en este proyecto; para una
    base SQLite existente, `create_all` no altera tablas ya creadas, asi que
    completamos las columnas nuevas a mano (ALTER TABLE ADD COLUMN).
    """
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        for column, ddl_type in USER_PROFILE_COLUMNS.items():
            if column not in existing:
                conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {column} {ddl_type}")
        conn.commit()


def init_db() -> None:
    """Crea las tablas (si no existen) y un usuario local por defecto."""
    from . import models  # noqa: F401  (registra los modelos en Base)

    Base.metadata.create_all(bind=engine)
    _ensure_user_profile_columns()

    db = SessionLocal()
    try:
        default_user = db.query(models.User).filter_by(id=1).first()
        if default_user is None:
            default_user = models.User(
                id=1,
                email="local@stickercontrol.local",
                name="Coleccionista Local",
                avatar=None,
            )
            db.add(default_user)
            db.commit()
    finally:
        db.close()
