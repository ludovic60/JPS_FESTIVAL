import scrapy


class BookItem(scrapy.Item):
    """Schéma commun rempli par tous les spiders, quel que soit le site source.

    L'ISBN est la clé de jointure prioritaire pour le croisement final ;
    à défaut, titre + auteur normalisés servent de repli (fuzzy matching).
    """

    source_site = scrapy.Field()
    url = scrapy.Field()
    titre = scrapy.Field()
    auteur = scrapy.Field()
    editeur = scrapy.Field()
    isbn = scrapy.Field()
    date_publication = scrapy.Field()
    prix = scrapy.Field()
