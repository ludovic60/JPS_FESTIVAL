"""Initialise (ou complète) le schéma SQLite. Utile pour inspecter/tester
la base avant même de lancer un spider — sinon elle est créée automatiquement
au premier `scrapy crawl`."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from book_scraper import db  # noqa: E402

if __name__ == "__main__":
    db.init_db()
    print(f"Base initialisée : {db.DB_PATH}")
