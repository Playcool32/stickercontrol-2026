"""
Importa figuritas desde un CSV a la tabla master_stickers (upsert por `code`).

Uso:
    py seed_db.py [ruta_csv]

Si no se pasa ruta, usa ../data/stickers_master.csv (dataset de PRUEBA con
4 paises + FWC). La tabla master_stickers se crea vacia en init_db() y se
puebla con este script; en el futuro este CSV sera reemplazado por una
exportacion real desde Google Sheets con el catalogo completo (~970
figuritas), siguiendo el mismo patron de columnas.

Columnas requeridas en el CSV:
    code, group, country_code, country_name, number, player_name_or_detail, type
"""

import csv
import sys
from pathlib import Path

from app.database import SessionLocal, init_db
from app.models import MasterSticker

REQUIRED_COLUMNS = {
    "code",
    "group",
    "country_code",
    "country_name",
    "number",
    "player_name_or_detail",
    "type",
}

DEFAULT_CSV_PATH = Path(__file__).resolve().parent.parent / "data" / "stickers_master.csv"


def load_rows(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Faltan columnas requeridas en {csv_path}: {sorted(missing)}")
        return list(reader)


def seed(csv_path: Path) -> None:
    rows = load_rows(csv_path)
    codes_in_csv = {row["code"].strip() for row in rows}

    db = SessionLocal()
    try:
        inserted = 0
        updated = 0
        for row in rows:
            code = row["code"].strip()
            group = row["group"].strip() or None

            existing = db.query(MasterSticker).filter(MasterSticker.code == code).first()
            values = {
                "code": code,
                "group": group,
                "country_code": row["country_code"].strip(),
                "country_name": row["country_name"].strip(),
                "number": int(row["number"]),
                "player_name_or_detail": row["player_name_or_detail"].strip(),
                "type": row["type"].strip(),
            }

            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
                updated += 1
            else:
                db.add(MasterSticker(**values))
                inserted += 1

        # Elimina codigos que ya no estan en el CSV (ej. dataset de prueba
        # reemplazado por el catalogo real), para que master_stickers
        # refleje exactamente el CSV fuente.
        deleted = (
            db.query(MasterSticker)
            .filter(~MasterSticker.code.in_(codes_in_csv))
            .delete(synchronize_session=False)
        )

        db.commit()
        print(
            f"OK: {inserted} insertadas, {updated} actualizadas, "
            f"{deleted} eliminadas (total {len(rows)} filas en {csv_path.name})"
        )
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else None
    path = Path(csv_arg).resolve() if csv_arg else DEFAULT_CSV_PATH
    if not path.exists():
        raise SystemExit(f"No se encontro el CSV: {path}")
    seed(path)
