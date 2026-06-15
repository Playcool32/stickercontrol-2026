import json
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # stickercontrol-2026/
COUNTRIES_JSON_PATH = PROJECT_ROOT / "data" / "countries.json"


@lru_cache
def load_countries() -> dict[str, dict]:
    if not COUNTRIES_JSON_PATH.exists():
        return {}
    data = json.loads(COUNTRIES_JSON_PATH.read_text(encoding="utf-8"))
    return {country["fifa_code"]: country for country in data}


def get_flag_path(fifa_code: str) -> str | None:
    country = load_countries().get(fifa_code)
    return country["flag_path"] if country else None


def get_album_order(fifa_code: str) -> int:
    """Posicion (1-4) de la seleccion dentro de su grupo, segun el orden real
    del album/sorteo. Si falta el dato (o es FWC/especiales), devuelve un
    valor alto para que quede al final sin romper el orden."""
    country = load_countries().get(fifa_code)
    order = country.get("album_order") if country else None
    return order if order is not None else 99
