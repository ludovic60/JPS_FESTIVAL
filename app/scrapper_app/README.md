# book_scraper — squelette Scrapy multi-sites

## 🗂️ Structure

```
book_scraper/
├── scrapy.cfg
├── requirements.txt
├── book_scraper/
│   ├── settings.py
│   ├── items.py             # Schéma unifié (BookItem)
│   ├── pipelines.py         # Normalisation + stockage SQLite
│   ├── middlewares.py
│   ├── db.py                # Anti-doublons + accès à la base unifiée
│   ├── db/scraped.sqlite    # Créée automatiquement au 1er run
│   ├── input/
│   │   └── predefined_urls.csv   # Mode "liste"
│   └── spiders/
│       ├── base_spider.py   # Logique commune : 3 modes + dédup
│       ├── site_a_spider.py # Exemple de site (sélecteurs à adapter)
│       └── site_b_spider.py # Exemple d'un site à structure différente
└── scripts/
    ├── init_db.py
    └── cross_reference.py   # Croisement final des données (pandas)
```

## 🚀 Installation

```bash
cd book_scraper
python -m venv .venv && source .venv/bin/activate   # ou l'équivalent Windows
pip install -r requirements.txt
```

## 🕸️ Les 3 modes de scraping

Chaque site a son propre spider, mais tous partagent les 3 mêmes modes,
pilotés en ligne de commande :

```bash
# Recherche par éditeur
scrapy crawl site_a -a mode=editeur -a query="Gallimard"

# Recherche par auteur
scrapy crawl site_b -a mode=auteur -a query="Victor Hugo"

# Liste prédéfinie d'URLs (lues dans book_scraper/input/predefined_urls.csv)
scrapy crawl site_a -a mode=liste
```

Voir/éditer `book_scraper/input/predefined_urls.csv` pour la 3ᵉ option —
une ligne par URL, avec la colonne `site` qui doit correspondre au `name`
du spider (`site_a`, `site_b`, …).

## 🔁 Anti-doublons

Chaque page individuelle (fiche livre) déjà scrapée avec succès est
enregistrée dans `book_scraper/db/scraped.sqlite` (table `scraped_pages`).
Au run suivant, elle est **automatiquement ignorée**, quel que soit le
mode utilisé pour y arriver (recherche éditeur, auteur, ou liste).

- Pour forcer un re-scrape malgré tout (ex: mise à jour de prix) :
  ```bash
  scrapy crawl site_a -a mode=liste -a force=1
  ```
- Les recherches éditeur/auteur déjà lancées sont aussi journalisées
  (table `searches`), à titre informatif — la recherche est quand même
  relancée à chaque fois pour capter les nouveautés, mais chaque page
  déjà connue est sautée individuellement.

## ➕ Ajouter un nouveau site

1. Crée `book_scraper/spiders/site_c_spider.py`, en copiant `site_a_spider.py`.
2. Fais hériter la classe de `BaseBookSpider`.
3. Implémente uniquement 3 méthodes propres à ce site :
   - `build_search_url(mode, query)`
   - `parse_search_results(response)`
   - `parse_item_page(response)`
4. Utilise `self._request_item_if_new(url)` (au lieu de `scrapy.Request`
   directement) partout où tu demandes une fiche livre — c'est ce qui
   déclenche la vérification anti-doublons.
5. Remplis un `BookItem` avec les mêmes noms de champs que les autres
   spiders (`titre`, `auteur`, `editeur`, `isbn`, `date_publication`, `prix`)
   pour que le croisement final fonctionne.

Astuce pour trouver les bons sélecteurs sans écrire de code :
```bash
scrapy shell "https://le-site-cible.fr/une-page-produit"
>>> response.css("h1::text").get()
```

## 🔗 Croiser les données une fois le scraping terminé

```bash
python scripts/cross_reference.py --out resultat.xlsx
```

Produit un fichier Excel à deux onglets :
- `croisement_isbn` : livres retrouvés sur plusieurs sites via l'ISBN (fiable).
- `croisement_fuzzy` : correspondances supplémentaires par similarité
  titre + auteur (utile quand l'ISBN manque ou diffère d'un site à l'autre),
  nécessite `rapidfuzz` (déjà dans requirements.txt).

## ⚙️ Paramètres importants (`settings.py`)

- `ROBOTSTXT_OBEY = True` — respecte le robots.txt de chaque site.
- `AUTOTHROTTLE_ENABLED` + `DOWNLOAD_DELAY` — limite la charge sur les
  sites cibles, s'adapte à leur temps de réponse.
- `scrapy-deltafetch` est proposé en commentaire comme filet de sécurité
  supplémentaire, indépendant de `book_scraper/db.py`.

## ⚠️ À adapter avant utilisation réelle

- Les sélecteurs CSS/XPath de `site_a_spider.py` et `site_b_spider.py`
  sont des **exemples fictifs** — à remplacer par les vrais sélecteurs
  des sites que tu cibles.
- Si un site charge son contenu via JavaScript, ajoute `scrapy-playwright`
  pour ce spider précis uniquement (`pip install scrapy-playwright`) —
  je peux t'aider à l'intégrer si besoin.
- Pense à vérifier les conditions d'utilisation de chaque site avant de
  le scraper à grande échelle.
