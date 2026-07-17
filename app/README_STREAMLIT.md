# Présence Week-end — Application Streamlit

Application Python (Streamlit) pour déclarer sa présence sur un week-end (Samedi/Dimanche
par créneaux) et indiquer les tâches souhaitées, avec un tableau récapitulatif en double entrée.

## Fonctionnalités
- Connexion / inscription (email + mot de passe, hachage bcrypt).
- Réinitialisation du mot de passe par lien email (SMTP Gmail).
- Rôles **Administrateur** et **Utilisateur**.
- Déclaration de présence : Samedi & Dimanche × Matinée / Après-midi / Soirée, avec case
  « Journée entière ».
- Sélection des tâches parmi une liste gérée par les administrateurs.
- Tableau récapitulatif double entrée : Tâches (lignes) × Jours&créneaux (colonnes) avec les noms.
- Espace admin : gérer les tâches (ajout/modif/suppression), **réinitialiser tous les votes**,
  **modifier / réinitialiser les votes d'une personne**.

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Déploiement sur Streamlit Community Cloud
1. Poussez ce dépôt sur GitHub.
2. Sur https://share.streamlit.io/deploy, choisissez le dépôt et le fichier `streamlit_app.py`.
3. Dans **Settings > Secrets**, collez le contenu de `.streamlit/secrets.toml.example` complété
   (admin, APP_URL, identifiants Gmail).

## Configuration (secrets)
Voir `.streamlit/secrets.toml.example`. Gmail nécessite un **mot de passe d'application** :
https://myaccount.google.com/apppasswords

## Stockage
Les données sont dans des fichiers plats JSON (`/data`) :
- `tasks.json` — liste des tâches (fichier plat lu par l'application),
- `users.json`, `presence.json`, `reset_tokens.json`.

⚠️ Sur Streamlit Cloud le système de fichiers est **éphémère** (données réinitialisées au
redéploiement). Pour une persistance durable et une base d'utilisateurs partagée entre
plusieurs applications (SSO léger), réimplémentez `weekend_app/storage.py` avec MongoDB Atlas
(les variables `MONGO_URL` / `DB_NAME` sont prévues dans les secrets).

## Design System réutilisable
`design_system.py` est autonome : copiez-le dans vos autres applications Streamlit et appelez
`inject()` après `st.set_page_config(...)`. Le thème global est aussi défini dans
`.streamlit/config.toml`.
