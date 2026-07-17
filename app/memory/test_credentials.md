# Identifiants de test — Application Streamlit

## Administrateur (seedé au démarrage)
- Email: admin@weekend.fr
- Password: admin123
- Rôle: admin

## Utilisateur
- À créer via l'onglet « Créer un compte » (rôle user).

## Configuration
- Secrets: voir `.streamlit/secrets.toml.example` (ADMIN_EMAIL, ADMIN_PASSWORD, APP_URL, Gmail SMTP).
- Lancement: `streamlit run streamlit_app.py` (port 8501).
- Données: fichiers plats JSON dans `/app/data/` (tasks.json, users.json, presence.json, reset_tokens.json).

## Note
Le lien de réinitialisation par email nécessite un mot de passe d'application Gmail
(GMAIL_ADDRESS + GMAIL_APP_PASSWORD dans les secrets). Sans SMTP configuré, le lien est affiché
en clair dans l'onglet « Mot de passe oublié » (mode dev).
