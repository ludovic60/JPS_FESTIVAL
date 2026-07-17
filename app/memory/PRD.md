# PRD — Application Présence Week-end (Streamlit)

## Problème initial
Application FR : se loguer, indiquer sa présence sur un week-end (Samedi/Dimanche) par créneaux
avec case "journée entière", choisir des tâches parmi une liste gérée par les administrateurs,
et afficher un tableau récapitulatif double entrée (Tâches × Jours/créneaux) avec les noms.
Contraintes ajoutées : réinitialisation mot de passe par email, rôles admin/user, admin peut
réinitialiser tous les votes ou ceux d'une personne, design-system réutilisable, tâches en
fichier plat, application lançable en Python depuis share.streamlit.io.

## Décision d'architecture (mise à jour)
- **PIVOT** : abandon de la version React+FastAPI au profit d'une **application Streamlit 100% Python**
  (déployable sur https://share.streamlit.io/deploy, entrée `streamlit_app.py`).
- Stockage : **fichiers plats JSON** dans `/app/data/` (couche `weekend_app/storage.py` abstraite,
  migrable vers MongoDB Atlas plus tard).
- Auth : email/mot de passe (bcrypt), session `st.session_state`, reset par email (SMTP Gmail),
  jetons de reset hachés (sha256) à usage unique + expiration 1h.
- SSO "léger" : base d'utilisateurs commune prévue via MongoDB Atlas partagé (à brancher).

## Structure
- `streamlit_app.py` — point d'entrée.
- `weekend_app/` : config, security, storage, email_utils, auth, views.
- `design_system.py` — module de thème réutilisable (autonome) + `.streamlit/config.toml`.
- `data/tasks.json` — fichier plat des tâches.

## Réalisé (2026-07-17)
- Connexion / inscription / mot de passe oublié (lien affiché en dev si SMTP absent).
- Présence Samedi/Dimanche × Matinée/Après-midi/Soirée + "Journée entière".
- Sélection des tâches ; tableau récapitulatif double entrée avec badges de noms.
- Admin : CRUD tâches (fichier plat), réinitialiser tous les votes, modifier/réinitialiser les
  votes d'une personne.
- Design system réutilisable + README de déploiement Streamlit.
- Logique validée par tests Python + captures d'écran de l'UI.

## Backlog / Prochaines étapes
- P0: Fournir GMAIL_ADDRESS + GMAIL_APP_PASSWORD (secrets) pour activer l'envoi réel d'email.
- P1: Brancher MongoDB Atlas (persistance + base d'utilisateurs partagée pour le SSO multi-apps).
- P1: Persistance de session (rester connecté après refresh) via cookies.
- P2: Export du récap (CSV/PDF), gestion de plusieurs week-ends datés.
