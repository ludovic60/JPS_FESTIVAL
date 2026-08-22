"""
Croise les données collectées sur tous les sites, à partir de la table
unifiée `books_raw` (remplie par le SQLiteStorePipeline pendant le scraping).

Usage :
    python scripts/cross_reference.py
    python scripts/cross_reference.py --out resultat.xlsx

Stratégie de jointure :
1. Priorité à l'ISBN quand il est disponible sur au moins 2 sites.
2. Repli en fuzzy matching (titre + auteur normalisés) pour les livres
   sans ISBN exploitable, via `rapidfuzz` (pip install rapidfuzz).
"""

import argparse
import sqlite3
import sys
import unicodedata
from pathlib import Path

import pandas as pd

DB_PATH = Path(__file__).resolve().parent.parent / "book_scraper" / "db" / "scraped.sqlite"


def load_books() -> pd.DataFrame:
    if not DB_PATH.exists():
        sys.exit(f"Base introuvable : {DB_PATH}. Lance d'abord un ou plusieurs spiders.")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM books_raw", conn)
    conn.close()
    return df


def normalize_text(value) -> str:
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return " ".join(value.lower().split())


def cross_by_isbn(df: pd.DataFrame) -> pd.DataFrame:
    with_isbn = df[df["isbn"].notna() & (df["isbn"] != "")]
    pivot = with_isbn.pivot_table(
        index="isbn",
        columns="source_site",
        values=["titre", "auteur", "editeur", "prix", "date_publication", "url"],
        aggfunc="first",
    )
    pivot.columns = [f"{col}_{site}" for col, site in pivot.columns]
    pivot["nb_sites"] = with_isbn.groupby("isbn")["source_site"].nunique()
    return pivot.reset_index().sort_values("nb_sites", ascending=False)


def fuzzy_cross_without_isbn(df: pd.DataFrame, threshold: int = 90) -> pd.DataFrame:
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("⚠️  rapidfuzz non installé (pip install rapidfuzz) — étape fuzzy ignorée.")
        return pd.DataFrame()

    without_isbn = df[df["isbn"].isna() | (df["isbn"] == "")].copy()
    without_isbn["key"] = (
        without_isbn["titre"].map(normalize_text) + " | " + without_isbn["auteur"].map(normalize_text)
    )

    matches = []
    seen = set()
    records = without_isbn.to_dict("records")
    for i, row_a in enumerate(records):
        if i in seen:
            continue
        group = [row_a]
        for j, row_b in enumerate(records[i + 1 :], start=i + 1):
            if j in seen or row_a["source_site"] == row_b["source_site"]:
                continue
            score = fuzz.token_sort_ratio(row_a["key"], row_b["key"])
            if score >= threshold:
                group.append(row_b)
                seen.add(j)
        if len(group) > 1:
            matches.append(group)

    rows = []
    for group in matches:
        merged = {"nb_sites": len(group)}
        for row in group:
            site = row["source_site"]
            merged[f"titre_{site}"] = row["titre"]
            merged[f"auteur_{site}"] = row["auteur"]
            merged[f"url_{site}"] = row["url"]
        rows.append(merged)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description="Croise les livres scrapés sur plusieurs sites.")
    parser.add_argument("--out", default="cross_reference_result.xlsx", help="Fichier de sortie (.xlsx ou .csv)")
    parser.add_argument("--fuzzy-threshold", type=int, default=90, help="Seuil de similarité (0-100)")
    args = parser.parse_args()

    df = load_books()
    print(f"{len(df)} lignes chargées depuis books_raw ({df['source_site'].nunique()} site(s)).")

    isbn_result = cross_by_isbn(df)
    fuzzy_result = fuzzy_cross_without_isbn(df, threshold=args.fuzzy_threshold)

    print(f"→ {len(isbn_result)} livres croisés par ISBN.")
    print(f"→ {len(fuzzy_result)} correspondances supplémentaires par similarité titre/auteur.")

    out_path = Path(args.out)
    if out_path.suffix == ".xlsx":
        with pd.ExcelWriter(out_path) as writer:
            isbn_result.to_excel(writer, sheet_name="croisement_isbn", index=False)
            fuzzy_result.to_excel(writer, sheet_name="croisement_fuzzy", index=False)
    else:
        isbn_result.to_csv(out_path, index=False)
        fuzzy_result.to_csv(out_path.with_stem(out_path.stem + "_fuzzy"), index=False)

    print(f"Résultat écrit dans : {out_path}")


if __name__ == "__main__":
    main()
