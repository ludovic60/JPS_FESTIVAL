"""
Deux pipelines exécutés dans l'ordre défini dans settings.py :

1. NormalizePipeline  : nettoie/normalise les champs (espaces, casse, ISBN).
2. SQLiteStorePipeline : écrit l'item dans la table unifiée `books_raw` et
                          marque la page comme scrapée dans `scraped_pages`
                          (utilisé par le mécanisme anti-doublons).
"""

import re

from itemadapter import ItemAdapter

from . import db


class NormalizePipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field in ("titre", "auteur", "editeur", "prix"):
            value = adapter.get(field)
            if value:
                adapter[field] = " ".join(value.split()).strip()

        isbn = adapter.get("isbn")
        if isbn:
            adapter["isbn"] = self._normalize_isbn(isbn)

        return item

    @staticmethod
    def _normalize_isbn(raw_isbn: str) -> str:
        return re.sub(r"[^0-9Xx]", "", raw_isbn).upper()


class SQLiteStorePipeline:
    def open_spider(self, spider):
        db.init_db()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        data = adapter.asdict()

        db.save_book(data)
        db.mark_page_scraped(
            site=data.get("source_site", spider.name),
            url=data.get("url"),
            isbn=data.get("isbn"),
        )
        return item
