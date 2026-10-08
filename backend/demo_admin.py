"""
Administracion de la base de la demo (StickerControl Demo Roura).

Uso (desde backend/, con el .env de la demo cargado):
    python demo_admin.py seed    # catalogo + coleccionistas ficticios; borra visitantes
    python demo_admin.py purge   # borra sandboxes vencidos (cron cada hora)
    python demo_admin.py reset   # borra todos los visitantes y regenera los coleccionistas (cron diario)
    python demo_admin.py stats   # conteos agregados

Salvaguardas:
- Requiere DEMO_MODE=true.
- Se niega a operar si la base contiene algun usuario que no sea demo
  (dominios *.demo.invalid), para que nunca corra sobre una base real.
"""

import sys

from app import demo, models
from app.database import DATABASE_URL, SessionLocal, init_db
from seed_db import DEFAULT_CSV_PATH, seed as seed_catalog


def _stats(db) -> str:
    visitors = db.query(models.User).filter(models.User.email.like(f"%{demo.VISITOR_DOMAIN}")).count()
    collectors = db.query(models.User).filter(models.User.email.like(f"%{demo.COLLECTOR_DOMAIN}")).count()
    stickers = db.query(models.MasterSticker).count()
    rows = db.query(models.UserSticker).count()
    return f"catalogo={stickers} coleccionistas={collectors} visitantes={visitors} filas_coleccion={rows}"


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in {"seed", "purge", "reset", "stats"}:
        print(__doc__)
        return 2
    if not demo.demo_enabled():
        print("ERROR: DEMO_MODE no esta activo. No se modifica ninguna base.")
        return 1

    command = argv[1]
    init_db()
    db = SessionLocal()
    try:
        demo.assert_demo_database(db)

        if command == "seed":
            db.close()
            seed_catalog(DEFAULT_CSV_PATH)
            db = SessionLocal()
            demo.delete_all_visitors(db)
            created = demo.seed_collectors(db)
            print(f"seed OK ({DATABASE_URL}): {created} coleccionistas. {_stats(db)}")
        elif command == "purge":
            deleted = demo.purge_expired_visitors(db)
            print(f"purge OK: {deleted} sandboxes vencidos borrados. {_stats(db)}")
        elif command == "reset":
            deleted = demo.delete_all_visitors(db)
            demo.seed_collectors(db)
            print(f"reset OK: {deleted} visitantes borrados, coleccionistas regenerados. {_stats(db)}")
        else:
            print(_stats(db))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
