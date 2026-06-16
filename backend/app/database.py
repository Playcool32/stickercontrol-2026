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


def _ensure_user_google_id_column() -> None:
    """Agrega `users.google_id` (Fase 2A) si falta, con indice unico.

    Mismo patron que _ensure_user_profile_columns: ALTER TABLE ADD COLUMN
    para bases SQLite existentes. SQLite no permite agregar una constraint
    UNIQUE via ALTER TABLE, por eso la columna se agrega sin constraint y
    el indice unico se crea aparte (los NULL no chocan entre si en SQLite).
    """
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "google_id" not in existing:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN google_id VARCHAR")
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"
        )
        conn.commit()


def _ensure_share_token_column() -> None:
    """Agrega `users.share_token` (Fase 2B) si falta, con indice unico."""
    with engine.connect() as conn:
        existing = {row[1] for row in conn.exec_driver_sql("PRAGMA table_info(users)")}
        if "share_token" not in existing:
            conn.exec_driver_sql("ALTER TABLE users ADD COLUMN share_token VARCHAR")
        conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_share_token ON users (share_token)"
        )
        conn.commit()


def init_db() -> None:
    """Crea las tablas (si no existen) y aplica migraciones livianas."""
    from . import models  # noqa: F401  (registra los modelos en Base)

    Base.metadata.create_all(bind=engine)
    _ensure_user_profile_columns()
    _ensure_user_google_id_column()
    _ensure_share_token_column()
