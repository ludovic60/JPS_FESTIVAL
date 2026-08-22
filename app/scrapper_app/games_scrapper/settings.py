BOT_NAME = "book_scraper"

SPIDER_MODULES = ["book_scraper.spiders"]
NEWSPIDER_MODULE = "book_scraper.spiders"

# --- Bonnes pratiques / politesse ---
ROBOTSTXT_OBEY = True
USER_AGENT = "book_scraper (+contact: votre-email@exemple.fr)"

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

DOWNLOAD_DELAY = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 4

RETRY_ENABLED = True
RETRY_TIMES = 3

# --- Pipelines : normalisation puis stockage unifié SQLite ---
ITEM_PIPELINES = {
    "book_scraper.pipelines.NormalizePipeline": 300,
    "book_scraper.pipelines.SQLiteStorePipeline": 400,
}

# --- Anti-doublons complémentaire (optionnel) ---
# La déduplication principale est gérée "manuellement" par book_scraper/db.py
# (table scraped_pages), ce qui permet de la piloter finement (mode liste,
# recherche déjà lancée, option --force, etc.).
#
# scrapy-deltafetch peut être activé en complément : il ignore automatiquement
# toute requête identique à une requête déjà traitée avec succès lors d'un run
# précédent, au niveau du framework (indépendamment de la logique métier).
# Décommenter ces lignes après `pip install scrapy-deltafetch` :
#
# SPIDER_MIDDLEWARES = {
#     "scrapy_deltafetch.DeltaFetch": 100,
# }
# DELTAFETCH_ENABLED = True

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

LOG_LEVEL = "INFO"
