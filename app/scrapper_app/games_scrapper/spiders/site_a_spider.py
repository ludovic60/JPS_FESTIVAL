"""
Exemple de spider pour un site fictif "site_a".

⚠️ Les sélecteurs CSS ci-dessous sont des EXEMPLES à remplacer par les
vrais sélecteurs du site que tu cibles (inspecte le HTML réel avec les
outils de dev du navigateur, ou `scrapy shell "https://..."`).
"""

from ..items import BookItem
from .base_spider import BaseBookSpider


class SiteASpider(BaseBookSpider):
    name = "site_a"
    allowed_domains = ["site-a.example.com"]  # à remplacer

    def build_search_url(self, mode: str, query: str) -> str:
        base = "https://site-a.example.com/recherche"
        param = "editeur" if mode == "editeur" else "auteur"
        return f"{base}?{param}={query}"

    def parse_search_results(self, response):
        # Liens vers chaque fiche livre trouvée dans les résultats de recherche
        for href in response.css("a.result-item::attr(href)").getall():
            item_url = response.urljoin(href)
            yield from self._request_item_if_new(item_url)

        # Pagination des résultats de recherche
        next_page = response.css("a.pagination-next::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_search_results,
                meta=response.meta,
            )

    def parse_item_page(self, response):
        item = BookItem()
        item["source_site"] = self.name
        item["url"] = response.url
        item["titre"] = response.css("h1.book-title::text").get()
        item["auteur"] = response.css(".book-author::text").get()
        item["editeur"] = response.css(".book-publisher::text").get()
        item["isbn"] = response.css(".book-isbn::text").get()
        item["date_publication"] = response.css(".book-pubdate::text").get()
        item["prix"] = response.css(".book-price::text").get()
        yield item
