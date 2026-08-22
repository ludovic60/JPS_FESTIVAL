"""
Couche d'accès à la base SQLite locale, partagée par tous les spiders.

Elle a deux rôles :
1. Anti-doublons : savoir si une page (site + url) a déjà été scrapée avec
   succès, pour ne jamais la re-télécharger inutilement.
2. Stockage unifié : une table `books_raw` où chaque site écrit ses données
   normalisées, qui sert ensuite de base au script de croisement
   (scripts/cross_reference.py).

Cette base est indépendante de scrapy-deltafetch (qui peut être activé en
complément dans settings.py) : elle donne un contrôle total et lisible,
utile puisqu'on croise plusieurs sites entre eux.
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent / "db" / "scraped.sqlite"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS scraped_pages (
            site TEXT NOT NULL,
            url TEXT NOT NULL,
            isbn TEXT,
            scraped_at TEXT NOT NULL,
            PRIMARY KEY (site, url)
        );

        CREATE TABLE IF NOT EXISTS searches (
            site TEXT NOT NULL,
            mode TEXT NOT NULL,
            query TEXT NOT NULL,
            last_run_at TEXT NOT NULL,
            PRIMARY KEY (site, mode, query)
        );

        CREATE TABLE IF NOT EXISTS books_raw (
            source_site TEXT NOT NULL,
            url TEXT NOT NULL,
            titre TEXT,
            auteur TEXT,
            editeur TEXT,
            isbn TEXT,
            date_publication TEXT,
            prix TEXT,
            scraped_at TEXT NOT NULL,
            PRIMARY KEY (source_site, url)
        );

        CREATE INDEX IF NOT EXISTS idx_books_isbn ON books_raw (isbn);
        """
    )
    conn.commit()
    conn.close()


def is_page_scraped(site: str, url: str) -> bool:
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM scraped_pages WHERE site = ? AND url = ?", (site, url)
    ).fetchone()
    conn.close()
    return row is not None


def mark_page_scraped(site: str, url: str, isbn: str | None = None) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO scraped_pages (site, url, isbn, scraped_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(site, url) DO UPDATE SET
            isbn = excluded.isbn,
            scraped_at = excluded.scraped_at
        """,
        (site, url, isbn, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def was_search_already_run(site: str, mode: str, query: str) -> bool:
    """Utile pour éviter de relancer une recherche éditeur/auteur identique."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM searches WHERE site = ? AND mode = ? AND query = ?",
        (site, mode, query),
    ).fetchone()
    conn.close()
    return row is not None


def mark_search_run(site: str, mode: str, query: str) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO searches (site, mode, query, last_run_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(site, mode, query) DO UPDATE SET last_run_at = excluded.last_run_at
        """,
        (site, mode, query, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def save_book(item: dict) -> None:
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO books_raw
            (source_site, url, titre, auteur, editeur, isbn, date_publication, prix, scraped_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_site, url) DO UPDATE SET
            titre = excluded.titre,
            auteur = excluded.auteur,
            editeur = excluded.editeur,
            isbn = excluded.isbn,
            date_publication = excluded.date_publication,
            prix = excluded.prix,
            scraped_at = excluded.scraped_at
        """,
        (
            item.get("source_site"),
            item.get("url"),
            item.get("titre"),
            item.get("auteur"),
            item.get("editeur"),
            item.get("isbn"),
            item.get("date_publication"),
            item.get("prix"),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()
