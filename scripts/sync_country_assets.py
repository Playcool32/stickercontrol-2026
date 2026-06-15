"""
sync_country_assets.py

Copia hacia este proyecto (stickercontrol-2026) los datos de paises y
banderas generados por el proyecto hermano en la raiz del repo
(ALBUM PANINI), que se descargan/regeneran con
`../../scripts/download_flags.py`.

Fuente (no se modifica):
    ../../data/countries.json
    ../../frontend/public/flags/*

Destino (se sobreescribe):
    ../data/countries.json
    ../frontend/public/flags/*

Uso:
    python scripts/sync_country_assets.py
"""

import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # stickercontrol-2026/
REPO_ROOT = PROJECT_ROOT.parent                          # ALBUM PANINI/

SRC_COUNTRIES_JSON = REPO_ROOT / "data" / "countries.json"
SRC_FLAGS_DIR = REPO_ROOT / "frontend" / "public" / "flags"

DEST_COUNTRIES_JSON = PROJECT_ROOT / "data" / "countries.json"
DEST_FLAGS_DIR = PROJECT_ROOT / "frontend" / "public" / "flags"


def main() -> int:
    if not SRC_COUNTRIES_JSON.exists():
        print(f"ERROR: no existe {SRC_COUNTRIES_JSON}")
        print("Ejecuta primero ../../scripts/download_flags.py en la raiz del repo.")
        return 1

    if not SRC_FLAGS_DIR.exists():
        print(f"ERROR: no existe {SRC_FLAGS_DIR}")
        print("Ejecuta primero ../../scripts/download_flags.py en la raiz del repo.")
        return 1

    DEST_COUNTRIES_JSON.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC_COUNTRIES_JSON, DEST_COUNTRIES_JSON)
    countries = json.loads(DEST_COUNTRIES_JSON.read_text(encoding="utf-8"))
    print(f"countries.json copiado ({len(countries)} paises) -> {DEST_COUNTRIES_JSON}")

    DEST_FLAGS_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for src_file in SRC_FLAGS_DIR.iterdir():
        if src_file.is_file():
            shutil.copyfile(src_file, DEST_FLAGS_DIR / src_file.name)
            count += 1
    print(f"{count} banderas copiadas -> {DEST_FLAGS_DIR}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
