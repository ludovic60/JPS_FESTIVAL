"""
Exemple de spider pour un site fictif "site_b", avec une structure d'URL et
de pagination différente de site_a — pour illustrer comment chaque site
gère ses propres spécificités tout en réutilisant la même logique de modes
et de déduplication.

⚠️ Sélecteurs et URLs à adapter au vrai site.
"""

from ..items import BookItem
from .base_spider import BaseBookSpider


class SiteBSpider(BaseBookSpider):
    name = "site_b"
    allowed_domains = ["site-b.example.com"]  # à remplacer

    def build_search_url(self, mode: str, query: str) -> str:
        # site_b utilise des chemins d'URL plutôt que des query params
        segment = "publisher" if mode == "editeur" else "author"
        return f"https://site-b.example.com/search/{segment}/{query}"

    def parse_search_results(self, response):
        for href in response.xpath("//div[@class='result']/a/@href").getall():
            item_url = response.urljoin(href)
            yield from self._request_item_if_new(item_url)

        # site_b pagine via un paramètre "page" plutôt qu'un lien "suivant"
        current_page = response.meta.get("page", 1)
        has_more_results = bool(response.css(".results-grid .card"))
        if has_more_results and current_page < 50:  # garde-fou anti-boucle infinie
            next_url = f"{response.url.split('?')[0]}?page={current_page + 1}"
            yield response.follow(
                next_url,
                callback=self.parse_search_results,
                meta={**response.meta, "page": current_page + 1},
            )

    def parse_item_page(self, response):
        item = BookItem()
        item["source_site"] = self.name
        item["url"] = response.url
        item["titre"] = response.xpath("//h1[@id='title']/text()").get()
        item["auteur"] = response.xpath("//span[@class='by']/text()").get()
        item["editeur"] = response.xpath("//td[@data-field='publisher']/text()").get()
        item["isbn"] = response.xpath("//td[@data-field='isbn']/text()").get()
        item["date_publication"] = response.xpath("//td[@data-field='date']/text()").get()
        item["prix"] = response.css(".price-tag::text").get()
        yield item
