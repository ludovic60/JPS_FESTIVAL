"""Vues Streamlit pour Bar à jeux."""


           
import logging
import pandas as pd
import streamlit as st
import bcrypt
import config_bar_jeux
import storage_jeux
import export
import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import commun.auth,  commun.config , commun.common_store
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def main_app(user):
    with st.sidebar:
        st.markdown("### 🎲 Bar à jeux")
        st.write(f"**{user['pseudo']}**")
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)
            pages = ["Jeux sortis depuis dernier festival", "Jeux sortis avant dernier festival", "Demandes d'ajout", "Liste suggestions", "Creation mot de passe", "Liste finale"]
        else : 
            pages = ["Jeux sortis depuis dernier festival", "Jeux sortis avant dernier festival", "Demandes d'ajout", "Liste finale"]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
        st.divider()
        if st.button("Déconnexion"):
            commun.auth.logout()
            st.rerun()

    if page == "Jeux sortis depuis dernier festival":
        months = config_bar_jeux.month_keys()
        label = st.selectbox("Mois", [l for _, l in months])
        key = next(k for k, l in months if l == label)
        _list_page(f"Jeux — {label}", key, user)
    elif page == "Jeux sortis avant dernier festival":
        _list_page("Vieux jeux", config_bar_jeux.VIEUX_KEY, user)
    elif page == "Demandes d'ajout":
        _requests_page(user)
    elif page == "Liste suggestions":
        _requests_suggestion_page(user)    
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
    #ckey = f"{list_key}::{str(g['_id'])}"
    ckey_this_game = f"{str(g['_id'])}"
    is_admin = user["role"] == "admin"
    admin_sel = storage_jeux.get_admin_selected()
    logging.info(f"liste jeu selectionne {admin_sel}")
    sugg = storage_jeux.get_suggestions()

   
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            if g.get("couverture"):
                st.image(g["couverture"], width="stretch")
        with c2:
            title = g.get("nom_jeu_complet") or g.get("nom_jeu") or "Jeu"
            # badge_nouv = " 🆕" if str(g.get("est_nouveaute", "")).lower() in ("oui", "true", "1") else ""
            # st.markdown(f"#### {title}{badge_nouv}")
            st.markdown(f"#### {title}")
            meta = " · ".join([x for x in [
                f"⭐ {g.get('classement_jps_final','')}" if g.get("classement_jps_final") else "",
                f"👥 {g.get('nombre_joueurs','')}" if g.get("nombre_joueurs") else "",
                f"🎂 {g.get('age_boite','')}" if g.get("age_boite") else "",
                f"⏱ {g.get('duree','')}" if g.get("duree") else "",
                
            ] if x])
            if meta:
                st.caption(meta)
            cc = st.columns(2)
            with cc[0]:
                if is_admin:
                     # 1. On ne garde que les suggestions spécifiques à CE jeu
                    select_this_game = [adsel for adsel in admin_sel if str(adsel.get("id_jeux")) == ckey_this_game]
                  
                    # 2.admin a retenu ce jeu ?
                    has_selected_this_game = [admin_sel[0]["id_jeux"] for sadmin in select_this_game]
                    val_admin=""  

                    def on_admin_change(ckey_this_game,mode):
                       logging.info(f"clic sur la checkbox retenu admin ")
                       storage_jeux.toggle_admin_selected(ckey_this_game, mode)
                       st.rerun()     

                           
                    if has_selected_this_game :
                             
                               val_admin = st.checkbox("Retenir (admin)", value= 1==1, key=f"s_admin_{ckey_this_game}", on_change=on_admin_change(ckey_this_game,"insert"))
                    else :            
                  
                               val_admin = st.checkbox("Retenir (admin)", value= 1==0, key=f"s_admin_{ckey_this_game}", on_change=on_admin_change(ckey_this_game,"delete"))
                    
                   
                       

                    
                else:
                     # 1. On ne garde que les suggestions spécifiques à CE jeu
                    select_this_game = [adsel for adsel in admin_sel if str(adsel.get("id_jeux")) == ckey_this_game]
                    
                    # 2.admin a retenu ce jeu ?
                    has_selected_this_game = [admin_sel[0]["id_jeux"] for sadmin in select_this_game]

                    if has_selected_this_game :
                        val_admin = st.markdown(":red[retenu dans selection final]")
                    
                    # 1. On ne garde que les suggestions spécifiques à CE jeu
                    sugg_this_game = [s for s in sugg if str(s.get("id_jeux")) == ckey_this_game]
                    
                    # 2. On extrait les IDs des utilisateurs ayant suggéré CE jeu
                    uids_this_game = [s["user_id"] for s in sugg_this_game]
                    
                    # 3. L'utilisateur a-t-il suggéré CE jeu ?
                    has_suggested = user["id"] in uids_this_game
                    
                    # 4. Affichage de la checkbox avec la bonne valeur
                    val_check_suggest = st.checkbox("Je suggère ce jeu", value=has_suggested, key=f"sug_{ckey_this_game}")
                    
                    # 5. Détection du clic réel (changement d'état pour ce jeu précis)
                    if val_check_suggest != has_suggested:
                        storage_jeux.toggle_suggestion(ckey_this_game, user["id"], val)
                        st.rerun()
                
                   
                    
            with cc[1]:
                list_sugg_this_game = [game for game in sugg if game["id_jeux"] == ckey_this_game]
    
                # 2. Compter combien il y en a
                nb_sugg = len(list_sugg_this_game)
                    
                st.caption(f"👍 {nb_sugg} suggestion(s)")
                if nb_sugg > 0  :
                    
                    if any(ckey_this_game in game["id_jeux"] for game in admin_sel): 
                        st.badge("✅ suggestion Retenu")
                    else : 
                        st.badge("suggestion à traiter")

            with st.expander("Détails du jeu"):
                for fk, fl in config_bar_jeux.GAME_FIELDS:
                    v = g.get(fk, "")
                    if v not in ("", None):
                        st.markdown(f"**{fl}** : {v}")


def _list_page(title, list_key, user):
    st.title(title)
    
    with st.expander("➕ Demander l'ajout d'un jeu"):
        with st.form(f"req_{list_key}", clear_on_submit=True):
            n = st.text_input("Nom du jeu")
            u = st.text_input("URL myludo")
            if st.form_submit_button("Envoyer la demande", type="primary") and n.strip():
                storage_jeux.add_request("ajout jeux", n, u, list_key, user["pseudo"])
                st.success("Demande envoyée à l'administrateur")

    games = storage_jeux.load_games(list_key)
    
    if not games:
        st.info("Aucun jeu dans cette liste.")
        return

    # Champ de saisie utilisateur
    search_query = st.text_input(
        "🔎 Rechercher un jeu (nom ou URL)",
        placeholder="Ex: Catan, https://...",
        key=f"game_search_input_{list_key}"  # Clé rendue unique par list_key
    ).strip().lower()

    # Filtrage de la liste de jeux
    filtered_games = []

    for g in games:
        title = (g.get("nom_jeu_complet") or g.get("nom_jeu") or "").lower()
        url = (g.get("url_myludo") or "").lower()  # Sécurisé avec str vide si None
        
        # Validation si le terme recherché est présent
        if not search_query or (search_query in title or search_query in url):
            filtered_games.append(g)

    # Affichage des cartes filtrées
    if filtered_games:
        per_row = 3
        # FIX : On utilise len(filtered_games) ici !
        for i in range(0, len(filtered_games), per_row):
            cols = st.columns(per_row)
            for j, g in enumerate(filtered_games[i:i + per_row]):
                with cols[j]:
                    _game_card(g, list_key, user)
    else:
        st.info("Aucun jeu ne correspond à votre recherche.")
    logging.info(f"Utilisateur sélectionné : )")
   
def _requests_suggestion_page(user):
    st.title("liste des suggestions par les joueurs")


def _requests_page(user):
    st.title("Demandes d'ajout de jeux")
    reqs = storage_jeux.get_requests("ajout jeux")
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
                    storage_jeux.remove_request(r["id"])
                    st.rerun()


def _final_page(user):
    st.title("Liste finale — Prêts")
    st.caption("Tableau croisé : jeux retenus par l'admin × personnes. Cochez les jeux que vous pouvez prêter.")
    finals = storage_jeux.final_games()
    print("finals")
    print(finals)
    logging.info(f"liste des jeux selec {finals} ")
    users = commun.common_store.get_users()
    loans = storage_jeux.get_loans()
    current_user = user
    is_admin = current_user == "admin"
    # emplacement reservé pour le bouton de validation du pret par les utilisateurs
    button_container = st.container()
    
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return
    rows = []
    for game in finals:
        print(game.get('id_jeux'))
        g = storage_jeux.get_info_games( game.get('id_jeux'))
        print( int(str(g[0].get("annee_parution"))) *100)
        print( int(str(g[0].get("mois_sortie")) ))
        print ( int(str(g[0].get("annee_parution"))) *100 +  int(str(g[0].get("mois_sortie")) ))       
        periode_parution = int(str(g[0].get("annee_parution"))) *100 +  int(str(g[0].get("mois_sortie")) )


        print((int( cs._secret("ANNEE_FESTIVAL"))-1) *100 )
        print( int(cs._secret("MOIS_FESTIVAL") )   )  
        logging.info(f"annee parution {g[0].get("annee_parution")}")
        logging.info(f"annee parution en int  {int(g[0].get("annee_parution"))}")
        logging.info(f"lmois de apurtion {g[0].get("mois_sortie")}")
        logging.info(f"lmois de parution en int {int(g[0].get("mois_sortie"))}")        
        if  ( int(str(g[0].get("annee_parution"))) *100 +  int(str(g[0].get("mois_sortie")) )  )  >  ( (int( cs._secret("ANNEE_FESTIVAL"))-1) *100  + int(cs._secret("MOIS_FESTIVAL") )   ) 
                    New = "NOUVEAUTE"
        else :   
                    New = ""
               
               
        row = {"nouveaute" : new, "Annee": g[0].get("annee"), "Categorie jeu": g[0].get("classement JPS final"), "Couverture Jeu": g[0].get("couverture"), "Jeu": g[0].get("nom_jeu_complet"), "Total coché": "" }
        #for u in users:
        #           for ul in loans:   
        #                      if ul[0].get("_id") ==   u[0].get("_id") and    ul[0].get("_id")   == g[0].get("_id")  :  
        #                          row[u[0].get("pseudo")] = 1
        rows.append(row)
    df = pd.DataFrame(rows)
    users_list = [u["pseudo"] for u in users]
    display_cols = ["Nouveauté"] +["Annee"] +["Categorie jeu"] +["Couverture Jeu"] +["Jeu"] +["Total coché"]+ users_list

    # Calcul du compteur par ligne
    st.session_state.df["Total coché"] = st.session_state.df[users_list].sum(axis=1)
  
    st.markdown(
        """
        <style>
        /* Agrandit la hauteur des cellules et conteneurs du tableau */
        [data-testid="stTable"] td, 
        div[data-testid="stDataEditor"] div[role="grid"] div[role="row"] {
            min-height: 100px !important;
            height: 500px !important;
        }
        /* Permet à l'image de prendre toute la hauteur disponible */
        div[data-testid="stDataEditor"] img {
            max-height: 5000px !important;
            object-fit: contain;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("📋 Grille de suivi")


        
       
    edited = st.dataframe(
            df[display_cols +["_ckey"]],
            column_config={
                "Couverture Jeu": st.column_config.ImageColumn(width=100),
                "Jeu": st.column_config.TextColumn(disabled=True) , 
                "Total coché" : st.column_config.NumberColumn(disabled=True)
            },
            hide_index =True, 
            width="stretch", 
            key ="loans_editor", 
            row_height=100 
            
    )

    # 5. TABLEAU RÉCAPITULATIF PAR PERSONNE ET TOTAL
    st.subheader("📊 Récapitulatif des validations")
    
    totaux_par_personne = df_edite[users_list].sum().to_dict()
    total_general = sum(totaux_par_personne.values())
    
    # Création du DataFrame récapitulatif
    df_recap = pd.DataFrame(
        list(totaux_par_personne.items()), 
        columns=["Personne", "Nombre de coches"]
    )
    # Affichage avec ligne de Total Général via les metrics ou un tableau
    col1, col2 = st.columns([2, 1])

    with col1:
        st.dataframe(df_recap, hide_index=True, width="stretch")

    with col2:
        st.metric(label="🎯 Total Général", value=total_general)
    

    with button_container:
        if st.button("Enregistrer les prêts", type="primary"):
            for r in edited.iterrows():
                ckey = df.loc[df["Jeu"] == r["Jeu"], "_ckey"].values[0]
                for u in users:
                    storage_jeux.set_loan(ckey, u["id"], bool(r[u["pseudo"]]))
            st.success("Prêts enregistrés")
            #st.rerun()
      
    
        

