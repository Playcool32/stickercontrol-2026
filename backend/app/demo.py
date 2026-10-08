"""
Modo demo (StickerControl Demo Roura).

Se activa con DEMO_MODE=true. Sin esa variable la app se comporta igual que
en produccion (login con Google). En modo demo:

- No hay Google OAuth: POST /api/auth/demo crea un "sandbox" por visitante,
  es decir, un usuario efimero con un album ficticio precargado.
- Los coleccionistas ficticios (publicos, fijos) los crea demo_admin.py.
  Las coincidencias de "Cerca" e "Intercambios" salen del algoritmo existente
  (crud.get_missing_and_duplicate_codes) aplicado a esos datos ficticios.
- Ningun usuario tiene telefono ni email reales: los links de WhatsApp/email
  nunca se generan.
- Los sandboxes vencen (DEMO_SESSION_TTL_HOURS) y se purgan; hay un tope de
  sandboxes simultaneos y un limite de creacion por IP.

Los usuarios se distinguen por el dominio del email (.invalid, RFC 2606),
sin columnas nuevas en la base.
"""

import os
import random
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timedelta

from sqlalchemy import insert
from sqlalchemy.orm import Session

from . import models

VISITOR_DOMAIN = "@visitor.demo.invalid"
COLLECTOR_DOMAIN = "@collector.demo.invalid"
VISITOR_NAME = "Visitante demo"

SESSION_EMAIL_KEY = "demo_email"
SESSION_EXPIRES_KEY = "demo_exp"

# Ubicacion aproximada asignada a todos los visitantes (centro de CABA), para
# que "Cerca" pueda calcular distancias sin pedir la ubicacion real.
VISITOR_CITY = "Buenos Aires (demo)"
VISITOR_LAT = -34.60
VISITOR_LON = -58.38

# Perfil del album precargado del visitante: semilla fija, mismo album para
# todos los visitantes.
VISITOR_TEMPLATE = {"seed": "visitor-template", "pasted": 0.55, "duplicates": 0.10, "loose": 12}

# Coleccionistas ficticios: nombres inventados, ciudades reales con
# coordenadas aproximadas, sin datos de contacto.
COLLECTORS = [
    {"slug": "lucia", "name": "Lucía (demo)", "city": "Palermo, CABA", "lat": -34.58, "lon": -58.42, "pasted": 0.72, "duplicates": 0.09},
    {"slug": "martin", "name": "Martín (demo)", "city": "Caballito, CABA", "lat": -34.62, "lon": -58.44, "pasted": 0.48, "duplicates": 0.07},
    {"slug": "sofia", "name": "Sofía (demo)", "city": "Vicente López", "lat": -34.53, "lon": -58.48, "pasted": 0.85, "duplicates": 0.12},
    {"slug": "tomas", "name": "Tomás (demo)", "city": "Quilmes", "lat": -34.72, "lon": -58.25, "pasted": 0.35, "duplicates": 0.05},
    {"slug": "valentina", "name": "Valentina (demo)", "city": "La Plata", "lat": -34.92, "lon": -57.95, "pasted": 0.63, "duplicates": 0.08},
    {"slug": "joaquin", "name": "Joaquín (demo)", "city": "Rosario", "lat": -32.95, "lon": -60.65, "pasted": 0.58, "duplicates": 0.10},
    {"slug": "camila", "name": "Camila (demo)", "city": "Córdoba", "lat": -31.42, "lon": -64.18, "pasted": 0.41, "duplicates": 0.06},
    {"slug": "bruno", "name": "Bruno (demo)", "city": "Mendoza", "lat": -32.89, "lon": -68.84, "pasted": 0.77, "duplicates": 0.11},
]


# ---------------------------------------------------------------------------
# Configuracion (se lee del entorno en cada llamada para que los tests
# puedan activar/desactivar el modo sin reimportar)
# ---------------------------------------------------------------------------

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except ValueError:
        return default


def demo_enabled() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"


def session_ttl_seconds() -> int:
    return _env_int("DEMO_SESSION_TTL_HOURS", 6) * 3600


def max_sandboxes() -> int:
    return _env_int("DEMO_MAX_SANDBOXES", 300)


def max_quantity() -> int:
    return _env_int("DEMO_MAX_QUANTITY", 20)


def max_notes_length() -> int:
    return _env_int("DEMO_MAX_NOTES_LENGTH", 280)


def is_visitor(user: models.User) -> bool:
    return user.email.endswith(VISITOR_DOMAIN)


def is_collector(user: models.User) -> bool:
    return user.email.endswith(COLLECTOR_DOMAIN)


# ---------------------------------------------------------------------------
# Limite de creacion de sandboxes por IP (en memoria; la app corre con un
# solo worker). El rate limiting general lo hace nginx.
# ---------------------------------------------------------------------------

class _RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits.setdefault(key, deque())
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            if len(self._hits) > 10_000:  # evita crecer sin limite
                self._hits = {k: v for k, v in self._hits.items() if v}
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


login_limiter = _RateLimiter()


def login_allowed(client_ip: str) -> bool:
    limit = _env_int("DEMO_LOGIN_RATE_LIMIT", 10)
    window = _env_int("DEMO_LOGIN_RATE_WINDOW_SECONDS", 600)
    return login_limiter.allow(client_ip, limit, window)


# ---------------------------------------------------------------------------
# Generacion determinista de colecciones ficticias
# ---------------------------------------------------------------------------

def build_collection(
    sticker_ids: list[int], *, seed: str, pasted: float, duplicates: float, loose: int = 0
) -> list[dict]:
    """Devuelve filas de user_stickers (sin user_id) para un perfil.

    - `pasted`: fraccion del catalogo pegada.
    - `duplicates`: fraccion del catalogo con repetidas (1 a 3), elegida
      entre las pegadas.
    - `loose`: figuritas conseguidas pero todavia sin pegar
      (DISPONIBLE_PARA_PEGAR).

    Misma semilla => misma coleccion, en cualquier base.
    """
    rng = random.Random(seed)
    ids = sorted(sticker_ids)
    n = len(ids)

    pasted_ids = set(rng.sample(ids, round(n * pasted)))
    dup_pool = sorted(pasted_ids) if pasted_ids else ids
    dup_ids = set(rng.sample(dup_pool, min(len(dup_pool), round(n * duplicates))))
    missing_pool = [i for i in ids if i not in pasted_ids]
    loose_ids = set(rng.sample(missing_pool, min(len(missing_pool), loose)))

    rows = []
    for sticker_id in ids:
        is_pasted = sticker_id in pasted_ids
        quantity = 0
        if sticker_id in dup_ids:
            quantity = rng.choice([1, 1, 1, 2, 2, 3])
        if sticker_id in loose_ids:
            quantity = 1
        if is_pasted or quantity:
            rows.append({"sticker_id": sticker_id, "quantity": quantity, "is_pasted": is_pasted})
    return rows


def _all_sticker_ids(db: Session) -> list[int]:
    return [row[0] for row in db.query(models.MasterSticker.id).all()]


def _insert_collection(db: Session, user_id: int, rows: list[dict]) -> None:
    if rows:
        now = datetime.utcnow()
        db.execute(
            insert(models.UserSticker),
            [{**row, "user_id": user_id, "notes": None, "updated_at": now} for row in rows],
        )


def _delete_users(db: Session, user_ids: list[int]) -> int:
    if not user_ids:
        return 0
    db.query(models.UserSticker).filter(models.UserSticker.user_id.in_(user_ids)).delete(
        synchronize_session=False
    )
    db.query(models.User).filter(models.User.id.in_(user_ids)).delete(synchronize_session=False)
    return len(user_ids)


# ---------------------------------------------------------------------------
# Sandboxes de visitantes
# ---------------------------------------------------------------------------

def purge_expired_visitors(db: Session, now: datetime | None = None) -> int:
    """Borra los sandboxes mas viejos que el TTL. Devuelve cuantos borro."""
    now = now or datetime.utcnow()
    cutoff = now - timedelta(seconds=session_ttl_seconds())
    ids = [
        row[0]
        for row in db.query(models.User.id)
        .filter(models.User.email.like(f"%{VISITOR_DOMAIN}"), models.User.created_at < cutoff)
        .all()
    ]
    deleted = _delete_users(db, ids)
    db.commit()
    return deleted


def _enforce_sandbox_cap(db: Session) -> None:
    """Si se alcanzo el tope, borra los sandboxes mas viejos para hacer lugar."""
    visitors = (
        db.query(models.User.id)
        .filter(models.User.email.like(f"%{VISITOR_DOMAIN}"))
        .order_by(models.User.created_at.asc(), models.User.id.asc())
        .all()
    )
    excess = len(visitors) - (max_sandboxes() - 1)
    if excess > 0:
        _delete_users(db, [row[0] for row in visitors[:excess]])


def delete_visitor(db: Session, user_id: int) -> None:
    user = db.get(models.User, user_id)
    if user is not None and is_visitor(user):
        _delete_users(db, [user_id])
        db.commit()


def create_visitor(db: Session) -> models.User:
    """Crea un sandbox nuevo con el album precargado."""
    purge_expired_visitors(db)
    _enforce_sandbox_cap(db)

    user = models.User(
        email=f"visitor-{uuid.uuid4().hex}{VISITOR_DOMAIN}",
        name=VISITOR_NAME,
        display_name=VISITOR_NAME,
        city=VISITOR_CITY,
        latitude=VISITOR_LAT,
        longitude=VISITOR_LON,
        is_public=False,
    )
    db.add(user)
    db.flush()

    rows = build_collection(_all_sticker_ids(db), **VISITOR_TEMPLATE)
    _insert_collection(db, user.id, rows)
    db.commit()
    db.refresh(user)
    return user


def start_session(session: dict, user: models.User) -> None:
    session["user_id"] = user.id
    session[SESSION_EMAIL_KEY] = user.email
    session[SESSION_EXPIRES_KEY] = int(time.time()) + session_ttl_seconds()


def session_is_valid(session: dict, user_id: int) -> bool:
    """La sesion es valida si no vencio y el sandbox sigue existiendo con el
    mismo email. Esto evita que una cookie vieja apunte a un id reutilizado
    por otro visitante despues de una purga o un reset."""
    from .database import SessionLocal

    expires = session.get(SESSION_EXPIRES_KEY)
    email = session.get(SESSION_EMAIL_KEY)
    if not expires or not email or time.time() > expires:
        return False

    db = SessionLocal()
    try:
        user = db.get(models.User, user_id)
        return user is not None and user.email == email and is_visitor(user)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Coleccionistas ficticios
# ---------------------------------------------------------------------------

def seed_collectors(db: Session) -> int:
    """Crea (o recrea) los coleccionistas ficticios con sus colecciones.
    Idempotente: borra los existentes y los vuelve a generar."""
    existing = [
        row[0]
        for row in db.query(models.User.id).filter(models.User.email.like(f"%{COLLECTOR_DOMAIN}")).all()
    ]
    _delete_users(db, existing)
    db.flush()

    sticker_ids = _all_sticker_ids(db)
    for c in COLLECTORS:
        user = models.User(
            email=f"collector-{c['slug']}{COLLECTOR_DOMAIN}",
            name=c["name"],
            display_name=c["name"],
            city=c["city"],
            latitude=c["lat"],
            longitude=c["lon"],
            is_public=True,
            contact_email=None,
            contact_whatsapp=None,
        )
        db.add(user)
        db.flush()
        rows = build_collection(
            sticker_ids, seed=f"collector-{c['slug']}", pasted=c["pasted"], duplicates=c["duplicates"]
        )
        _insert_collection(db, user.id, rows)

    db.commit()
    return len(COLLECTORS)


def delete_all_visitors(db: Session) -> int:
    ids = [
        row[0] for row in db.query(models.User.id).filter(models.User.email.like(f"%{VISITOR_DOMAIN}")).all()
    ]
    deleted = _delete_users(db, ids)
    db.commit()
    return deleted


def assert_demo_database(db: Session) -> None:
    """Salvaguarda: las operaciones destructivas del modo demo solo corren si
    la base contiene unicamente usuarios demo (nunca una base real)."""
    foreign = (
        db.query(models.User.id)
        .filter(
            ~models.User.email.like(f"%{VISITOR_DOMAIN}"),
            ~models.User.email.like(f"%{COLLECTOR_DOMAIN}"),
        )
        .count()
    )
    if foreign:
        raise RuntimeError(
            f"La base tiene {foreign} usuario(s) que no son demo: no se ejecuta ninguna "
            "operacion de demo sobre una base real."
        )
