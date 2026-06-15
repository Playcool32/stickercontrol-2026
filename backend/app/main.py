import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .database import init_db
from .routes import auth, collection, nearby, profile, reports, stickers, trades

app = FastAPI(title="StickerControl 2026 API")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-insecure-session-secret")
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"

# SessionMiddleware antes (mas adentro): mantiene la cookie de sesion
# (login Google, Fase 2A). CORSMiddleware al final (mas afuera): permite
# enviar/recibir esa cookie desde el origen del frontend (allow_credentials).
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="sc_session",
    same_site="lax",
    https_only=SESSION_COOKIE_SECURE,
    max_age=60 * 60 * 24 * 30,  # 30 dias - sesion persistente
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


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def health():
    return {"status": "ok", "app": "StickerControl 2026"}
