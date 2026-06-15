import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routes import collection, nearby, profile, reports, stickers, trades

app = FastAPI(title="StickerControl 2026 API")

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
