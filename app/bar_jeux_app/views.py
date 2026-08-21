"""Vues Streamlit pour Bar à jeux."""
import pandas as pd
import streamlit as st
import bcrypt
import auth, storage, config, export


def login_view():
    st.title("Bar à jeux")
    st.caption("Connectez-vous pour suggérer et prêter des jeux.")
    t1, t2 = st.tabs(["Connexion", "Créer un compte"])
    with t1:
        with st.form("j_login"):
            ps = st.text_input("pseudo")
            if not ps :
                ps = " "
            e = st.text_input("Email")   
            if not e :
                e = " "
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", type="primary"):
                err = auth.login(ps, e, p)
                st.error(err) if err else st.rerun()
    with t2:
        with st.form("j_reg"):
            n = st.text_input("Nom")
            e = st.text_input("Email", key="je")
            p = st.text_input("Mot de passe", type="password", key="jp")
            if st.form_submit_button("S'inscrire", type="primary"):
                err = auth.register(n, e, p)
                st.error(err) if err else st.rerun()


def main_app(user):
    with st.sidebar:
        st.markdown("### 🎲 Bar à jeux")
        st.write(f"**{user['pseudo']}**")
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)
            pages = ["Jeux du mois", "Vieux jeux", "Demandes d'ajout", "Creation mot de passe", "Liste finale"]
        else : 
            pages = ["Jeux du mois", "Demandes d'ajout", "Creation mot de passe", "Liste finale"]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
        st.divider()
        if st.button("Déconnexion"):
            auth.logout()
            st.rerun()

    if page == "Jeux du mois":
        months = config.month_keys()
        label = st.selectbox("Mois", [l for _, l in months])
        key = next(k for k, l in months if l == label)
        _list_page(f"Jeux — {label}", key, user)
    elif page == "Vieux jeux":
        _list_page("Vieux jeux", config.VIEUX_KEY, user)
    elif page == "Demandes d'ajout":
        _requests_page(user)
    elif page == "Creation mot de passe":
        _password_page(user)
    else:
        _final_page(user)



def _password_page(user):
    st.set_page_config(page_title="Générateur de Hash Bcrypt", page_icon="🔑")
    
    st.title("🔑 Générateur de Hash Bcrypt")
    st.write("Saisissez un mot de passe ci-dessous pour obtenir sa version hachée.")
    
    ## # Champ de saisie sécurisé
    password_input = st.text_input("Mot de passe à hacher", type="password")
    
    if st.button("Générer le hash"):
       if password_input:
            # Convertit le texte en octets
            password_bytes = password_input.encode('utf-8')
            # Génère un sel et hache le mot de passe
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password_bytes, salt)
            # Retourne la chaîne encodée à stocker en base                 
            hashed_result = hashed.decode('utf-8') 
            st.success("Mot de passe haché avec succès !")
           
            # Affichage du résultat dans un bloc de code pour faciliter le copie-coller
            st.code(hashed_result, language="text")
             
            st.info("💡 **Remarque :** En raison du salage aléatoire de Bcrypt, chaque clic générera une empreinte différente, même pour un mot de passe identique.")
    else:
        st.warning("Veuillez saisir un mot de passe avant de cliquer.")


def _game_card(g, list_key, user):
    ckey = f"{list_key}::{g['id']}"
    is_admin = user["role"] == "admin"
    admin_sel = storage.get_admin_selected()
    sugg = storage.get_suggestions()
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            if g.get("couverture"):
                st.image(g["couverture"], use_container_width=True)
        with c2:
            title = g.get("nom_jeu_complet") or g.get("nom_jeu") or "Jeu"
            badge_nouv = " 🆕" if str(g.get("est_nouveaute", "")).lower() in ("oui", "true", "1") else ""
            st.markdown(f"#### {title}{badge_nouv}")
            meta = " · ".join([x for x in [
                f"👥 {g.get('nombre_joueurs','')}" if g.get("nombre_joueurs") else "",
                f"🎂 {g.get('age_boite','')}" if g.get("age_boite") else "",
                f"⏱ {g.get('duree','')}" if g.get("duree") else "",
                f"⭐ {g.get('note_finale','')}" if g.get("note_finale") else "",
            ] if x])
            if meta:
                st.caption(meta)
            cc = st.columns(2)
            with cc[0]:
                if is_admin:
                    val = st.checkbox("Retenir (admin)", value=ckey in admin_sel, key=f"adm_{ckey}")
                    if val != (ckey in admin_sel):
                        storage.toggle_admin_selected(ckey, val)
                        st.rerun()
                else:
                    uids = set(sugg.get(ckey, []))
                    val = st.checkbox("Je suggère ce jeu", value=user["_id"] in uids, key=f"sug_{ckey}")
                    if val != (user["_id"] in uids):
                        storage.toggle_suggestion(ckey, user["_id"], val)
                        st.rerun()
            with cc[1]:
                st.caption(f"👍 {len(sugg.get(ckey, []))} suggestion(s)")
                if is_admin:
                    st.caption("✅ Retenu" if ckey in admin_sel else "")
            with st.expander("Détails du jeu"):
                for fk, fl in config.GAME_FIELDS:
                    v = g.get(fk, "")
                    if v not in ("", None):
                        st.markdown(f"**{fl}** : {v}")


def _list_page(title, list_key, user):
    st.title(title)
    st.caption("Fichier lu : `data/jeux/jeux_%s.json`" % list_key)
    with st.expander("➕ Demander l'ajout d'un jeu"):
        with st.form(f"req_{list_key}", clear_on_submit=True):
            n = st.text_input("Nom du jeu")
            u = st.text_input("URL myludo")
            if st.form_submit_button("Envoyer la demande", type="primary") and n.strip():
                storage.add_request(n, u, list_key, user["pseudo"])
                st.success("Demande envoyée à l'administrateur")
    games = storage.load_games(list_key)
    if not games:
        st.info("Aucun jeu dans cette liste. Ajoutez des jeux dans le fichier JSON correspondant.")
    per_row = 3
    for i in range(0, len(games), per_row):
        cols = st.columns(per_row)
        for j, g in enumerate(games[i:i + per_row]):
            with cols[j]:
                _game_card(g, list_key, user)


def _requests_page(user):
    st.title("Demandes d'ajout de jeux")
    reqs = storage.get_requests()
    if not reqs:
        st.info("Aucune demande.")
        return
    for r in reqs:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"**{r['name']}** — demandé par {r['by']}")
            if r.get("myludo_url"):
                c1.markdown(f"[Lien myludo]({r['myludo_url']}) · liste : `{r['list_key']}`")
            if user["role"] == "admin":
                if c2.button("Retirer", key=f"rmreq_{r['id']}"):
                    storage.remove_request(r["id"])
                    st.rerun()


def _final_page(user):
    st.title("Liste finale — Prêts")
    st.caption("Tableau croisé : jeux retenus par l'admin × personnes. Cochez les jeux que vous pouvez prêter.")
    finals = storage.final_games()
    users = storage.get_users()
    loans = storage.get_loans()
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return

    if user["role"] == "admin":
        rows = []
        for ckey, g in finals:
            row = {"Nouveauté": g.get("nom_jeu_complet"), "Categorie jeu": g.get("nom_jeu_complet"), "Couverture Jeu": g.get("nom_jeu_complet"), "Jeu": g.get("nom_jeu_complet") or g.get("nom_jeu"), "_ckey": ckey}
            for u in users:
                row[u["pseudo"]] = u["_id"] in set(loans.get(ckey, []))
            rows.append(row)
        df = pd.DataFrame(rows)
        display_cols = ["Nouveauté"] +["Categorie jeu"] +["Couverture Jeu"] +["Jeu"] + [u["pseudo"] for u in users]
        edited = st.data_editor(
            df[display_cols + ["_ckey"]],
            column_config={"_ckey": None, "Jeu": st.column_config.TextColumn(disabled=True)},
            hide_index=True, use_container_width=True, key="loans_editor",
        )
        if st.button("Enregistrer les prêts", type="primary"):
            for _, r in edited.iterrows():
                ckey = df.loc[df["Jeu"] == r["Jeu"], "_ckey"].values[0]
                for u in users:
                    storage.set_loan(ckey, u["id"], bool(r[u["pseudo"]]))
            st.success("Prêts enregistrés")
            st.rerun()
    else:
        for ckey, g in finals:
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                if g.get("couverture"):
                    c1.image(g["couverture"], use_container_width=True)
                title = g.get("nom_jeu_complet") or g.get("nom_jeu")
                c2.markdown(f"#### {title}")
                lenders = [u["name"] for u in users if u["id"] in set(loans.get(ckey, []))]
                c2.caption("Prêteurs : " + (", ".join(lenders) if lenders else "aucun"))
                mine = user["id"] in set(loans.get(ckey, []))
                val = c2.checkbox("Je peux prêter ce jeu", value=mine, key=f"loan_{ckey}")
                if val != mine:
                    storage.toggle_loan(ckey, user["id"], val)
                    st.rerun()
