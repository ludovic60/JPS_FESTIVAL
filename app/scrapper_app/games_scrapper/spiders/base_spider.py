"""
Spider de base : porte toute la logique commune (modes de lancement,
déduplication). Chaque site n'a qu'à hériter de cette classe et implémenter
3 méthodes spécifiques à sa structure HTML/URL :

    build_search_url(mode, query)   -> construit l'URL de recherche du site
    parse_search_results(response)  -> extrait les liens vers les fiches livre
    parse_item_page(response)       -> extrait les données d'une fiche livre

Utilisation en ligne de commande :

    scrapy crawl site_a -a mode=editeur -a query="Gallimard"
    scrapy crawl site_b -a mode=auteur  -a query="Victor Hugo"
    scrapy crawl site_a -a mode=liste
    scrapy crawl site_a -a mode=liste -a force=1   # ignore le cache anti-doublons
"""

import csv
from pathlib import Path

import scrapy

from .. import db

INPUT_DIR = Path(__file__).resolve().parent.parent / "input"


class BaseBookSpider(scrapy.Spider):
    """À hériter — ne pas lancer directement (pas de `name` défini ici)."""

    def __init__(self, mode=None, query=None, force=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if mode not in ("editeur", "auteur", "liste"):
            raise ValueError(
                "Argument -a mode=... requis, valeurs possibles : "
                "'editeur', 'auteur' ou 'liste'."
            )
        if mode in ("editeur", "auteur") and not query:
            raise ValueError(f"Le mode '{mode}' requiert -a query=\"...\"")

        self.mode = mode
        self.query = query
        self.force = bool(force)  # -a force=1 pour ignorer le cache anti-doublons
        db.init_db()

    def start_requests(self):
        if self.mode in ("editeur", "auteur"):
            if not self.force and db.was_search_already_run(self.name, self.mode, self.query):
                self.logger.info(
                    f"Recherche '{self.mode}={self.query}' déjà lancée pour {self.name} "
                    f"— relance quand même pour capter les nouveautés (pages déjà vues seront ignorées)."
                )
            url = self.build_search_url(self.mode, self.query)
            yield scrapy.Request(
                url,
                callback=self.parse_search_results,
                meta={"mode": self.mode, "query": self.query},
            )

        elif self.mode == "liste":
            for url in self._load_predefined_urls():
                yield from self._request_item_if_new(url)

    def closed(self, reason):
        if self.mode in ("editeur", "auteur") and reason == "finished":
            db.mark_search_run(self.name, self.mode, self.query)

    # --- Anti-doublons : point de passage unique pour demander une fiche livre ---
    def _request_item_if_new(self, url: str):
        if not self.force and db.is_page_scraped(self.name, url):
            self.logger.debug(f"Déjà scrapé, ignoré : {url}")
            return
        yield scrapy.Request(url, callback=self.parse_item_page)

    def _load_predefined_urls(self) -> list[str]:
        csv_path = INPUT_DIR / "predefined_urls.csv"
        if not csv_path.exists():
            self.logger.warning(f"Fichier introuvable : {csv_path}")
            return []
        with open(csv_path, newline="", encoding="utf-8") as f:
            return [
                row["url"]
                for row in csv.DictReader(f)
                if row.get("site") == self.name and row.get("url")
            ]

    # --- À implémenter dans chaque spider de site ---
    def build_search_url(self, mode: str, query: str) -> str:
        raise NotImplementedError

    def parse_search_results(self, response):
        raise NotImplementedError

    def parse_item_page(self, response):
        raise NotImplementedError
