import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from . import demo
from .database import init_db
from .routes import auth, collection, nearby, profile, reports, share, stickers, trades

DEFAULT_SESSION_SECRET = "dev-insecure-session-secret"
DEMO_MODE = demo.demo_enabled()

# En modo demo (instancia publica) no se exponen /docs ni /openapi.json.
app = FastAPI(
    title="StickerControl 2026 API",
    docs_url=None if DEMO_MODE else "/docs",
    redoc_url=None if DEMO_MODE else "/redoc",
    openapi_url=None if DEMO_MODE else "/openapi.json",
)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

SESSION_SECRET = os.getenv("SESSION_SECRET", DEFAULT_SESSION_SECRET)
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

if DEMO_MODE and (SESSION_SECRET == DEFAULT_SESSION_SECRET or len(SESSION_SECRET) < 32):
    raise RuntimeError("DEMO_MODE requiere un SESSION_SECRET propio de al menos 32 caracteres.")

# Demo: la cookie dura lo mismo que el sandbox; produccion: 30 dias.
SESSION_MAX_AGE = demo.session_ttl_seconds() if DEMO_MODE else 60 * 60 * 24 * 30

# SessionMiddleware antes (mas adentro): mantiene la cookie de sesion
# (login Google, Fase 2A). CORSMiddleware al final (mas afuera): permite
# enviar/recibir esa cookie desde el origen del frontend (allow_credentials).
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="sc_session",
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
    max_age=SESSION_MAX_AGE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(stickers.router)
app.include_router(collection.router)
app.include_router(reports.router)
app.include_router(trades.router)
app.include_router(profile.router)
app.include_router(nearby.router)
app.include_router(share.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def health():
    return {"status": "ok", "app": "StickerControl 2026"}


@app.get("/api/health")
def api_health():
    """Health check accesible via nginx (/api/health), usado por verify.sh."""
    return {"status": "ok", "demo": DEMO_MODE}
