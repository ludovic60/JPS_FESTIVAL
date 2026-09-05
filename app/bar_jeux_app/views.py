"""Vues Streamlit pour Bar à jeux."""


from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode           
import logging
import plotly.express as px
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

import commun.auth,  commun.config 
import commun.common_store as cs
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
    
    sugg = storage_jeux.get_suggestions()
    has_selected_this_game=""  
    select_this_game=""

           
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

            ##### gestion du classement =      
            if g.get("classement_jps_final") :
                    if g.get("classement_jps_final") == "FAMILLE":
                               classement = f"⚪⚪⚪ {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "INITIE":
                               classement = f"🟡⚪⚪ {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "EXPERT":
                               classement = f"🔴🔴⚪ {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "EXPERT+":
                               classement = f"🔴🔴🔴 {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "ENFANT":
                               classement = f"🧸 {g.get('classement_jps_final','')}"                                        
                    elif g.get("classement_jps_final") == "JEU DUO":
                                classement = f"👥 {g.get('classement_jps_final','')}"                                       
                    elif g.get("classement_jps_final") == "COOP/SEMI COOP":
                               classement = f"🤝 {g.get('classement_jps_final','')}"                             
                    elif g.get("classement_jps_final") == "ENQUETE/ESCAPE/ENIGME/CASSETETE":
                               classement = f"🕵️ {g.get('classement_jps_final','')}"                            
                    elif g.get("classement_jps_final") == "AMBIANCE":
                               classement = f"🎉 {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "NON CLASSE":
                               classement = f"🤔 {g.get('classement_jps_final','')}"
                    elif g.get("classement_jps_final") == "PBM CLASSEMENT":
                               classement = f"❓ {g.get('classement_jps_final','')}"
                    else : 
                               classement = f"❓❓❓ {g.get('classement_jps_final','')}"
            else :
                         classement = ""           

            meta = " · ".join([x for x in [
               classement,
                f"👥 {g.get('nombre_joueurs','')}" if g.get("nombre_joueurs") else "",
                f"🎂 {g.get('age_boite','')}" if g.get("age_boite") else "",
                f"⏱ {g.get('duree','')}" if g.get("duree") else "",
                
            ] if x])
            if meta:
                st.caption(meta)
            cc = st.columns(2)
            with cc[0]:
                     
                if is_admin:
                    # 1
                    select_this_game = [adsel for adsel in admin_sel if str(adsel.get("id_jeux")) == ckey_this_game]
                    # 2.admin a deja retenu auparavant 
                    has_selected_this_game = [admin_sel[0]["id_jeux"] for sadmin in select_this_game]  

                    # Callback exécuté uniquement lors d'un VRAI clic utilisateur
                    def on_admin_change(game_id, currently_selected):
                        mode = "delete" if currently_selected else "insert"
                
                        storage_jeux.toggle_admin_selected(game_id, mode)
                        if mode == insert :
                                   toggle_admin_selected(game_id, "update")
                                   
                    # Passe la fonction SANS les parenthèses () et utilise args=
                    st.checkbox(
                        "Retenir (admin)",
                        value=has_selected_this_game,
                        key=f"s_admin_{ckey_this_game}",
                        on_change=on_admin_change,
                        args=(ckey_this_game, has_selected_this_game),
                    )                                
                       

                    
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

           
                # 2. Compter combien il y en a
                nb_sugg = storage_jeux.get_game_nb_suggestions(ckey_this_game)
                    
                st.caption(f"👍 {nb_sugg} suggestion(s)")
                if nb_sugg > 0  :
 
                    statut = storage_jeux.get_game_suggestions(ckey_this_game)[0].get("statut")
                   
 
                    if statut == "suggestion Retenue":
                               st.badge("✅ suggestion Retenu")
                    elif statut == "suggestion refusée":   
                       
                                st.badge("❌ suggestion refusée")
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
    # --- EXTRACTION DES DONNEES UTILES ---
        #--- liste des jeux
    finals = storage_jeux.final_games()
   
   
    users = cs.get_users()
    loans = storage_jeux.get_loans()
    current_user = user
    is_admin = current_user == "admin"

    pseudo_list = list(u["pseudo"] for u in users)

           
    # emplacement reservé pour le bouton de validation du pret par les utilisateurs
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return           
    
    # creation des lignes du futur tableau croisé         
    row_jeux = []
    for game in finals:
        
        g = storage_jeux.get_info_games( game.get('id_jeux'))
      
        if ( g[0].get("mois_sortie")  and  g[0].get("annee_parution") ) :      
       
                   periode_parution = int(str(g[0].get("annee_parution"))) *100 +  int(str(g[0].get("mois_sortie")) )
                   periode_dernier_festival = (int( cs._secret("ANNEE_FESTIVAL"))-1) *100 + int(cs._secret("MOIS_FESTIVAL") )
           
                      
                   if periode_parution  >  periode_dernier_festival :
                               New = "NOUVEAUTE"
                   else :   
                               New = ""
        else :
                   New = ""                    
               
               
        row = {"nouveaute" : New, "Annee": g[0].get("annee"), "Categorie jeu": g[0].get("classement JPS final"), "Couverture Jeu": g[0].get("couverture"), "Jeu": g[0].get("nom_jeu_complet"), "Total coché par joueur": "" , "Total coché validé par admin": "" }
        row_jeux.append(row)
               
    #if "df_jeux" not in st.is_distinct:   
    df_jeux = st.session_state.df_jeux = pd.DataFrame(row_jeux)   
               
    # creation des colonnes du futur tableau croisé   avec preparation des checkbox
      
    if "grid_state" not in st.session_state:
         st.session_state.grid_state = {
         (select_joueur, valid_admin): [False, False]
         for select_joueur in st.session_state.df_jeux["Jeu"]
         for valid_admin in pseudo_list
     }
           

   #           for ul in loans:   
   #                           if ul[0].get("_id") ==   u[0].get("_id") and    ul[0].get("_id")   == g[0].get("_id")  :  
   #                          row[u[0].get("pseudo")] = 1      


   # --- CALCUL DES DONNÉES COMPLÉMENTAIRES ---
   # df_p = st.session_state.df_produits.copy()

   # Traitement des compteurs

    for j in pseudo_list:
         st.session_state.df_jeux[f"{j}_user"] = df_jeux["Jeu"].apply(
            lambda pid: st.session_state.grid_state[(pid, j)][0]
         )
         st.session_state.df_jeux[f"{j}_admin"] = df_jeux["Jeu"].apply(
            lambda pid: st.session_state.grid_state[(pid, j)][1]
        )

    # Compteurs par jeux
    st.session_state.df_jeux["Total coché par joueur"] = st.session_state.df_jeux[[f"{j}_user" for j in pseudo_list]].sum(axis=1)
    st.session_state.df_jeux["Total coché validé par admin"] = st.session_state.df_jeux[[f"{j}_admin" for j in pseudo_list]].sum(axis=1) 

    # Compteurs par joueur
    user_by_player = {j: st.session_state.df_jeux[f"{j}_user"].sum() for j in pseudo_list}
    admin_by_player = {j: st.session_state.df_jeux[f"{j}_admin"].sum() for j in pseudo_list}

    # --- PARTIE SUPERIEURE : GRAPHIQUES ---

    col_graph1, col_graph2, col_graph3 = st.columns(3)


    ###########---- 1. Histogramme par joueur (Validés vs Cochés Utilisateur)

    with col_graph1:
    
          st.subheader("Validations par Joueur")
          nb_jeux_histogramme = []
          for u in pseudo_list:
                   nb_jeux_histogramme.append(
                       {"Utilisateur": u, "Nb jeux": "pret par user", "Valeur": user_by_player[j]}
                   )
                   nb_jeux_histogramme.append({"Utilisateur": u, "Nb jeux": "pret validé (Admin)", "Valeur": admin_by_player[j]})
          df_jeux_histogramme  = pd.DataFrame(nb_jeux_histogramme)
               
          fig_hist = px.bar(
              df_jeux_histogramme,
              x="Utilisateur",
              y="Valeur",
              color="Nb jeux",
              barmode="group",
              color_discrete_map={"pret par user": "#636EFA", "pret validé (Admin)": "#2CA02C"},
          )
          st.plotly_chart(fig_hist, use_container_width=True)

    ###########----2. Camembert Nouveautés (jeux cochés au moins une fois par un utilisateur)
    with col_graph2:
          st.subheader("Produits cochés par Nouveauté")
          df_cochis = df_jeux_histogramme[df_jeux_histogramme["Valeur"] > 0]
          if not df_cochis.empty:
              df_nov = (
                  df_cochis["nouveaute"]
                  .map({True: "Nouveauté", False: "Ancien"})
                  .value_counts()
                  .reset_index()
              )
              df_nov.columns = ["Type", "Nombre"]
              fig_pie_nov = px.pie(df_nov, names="Type", values="Nombre", hole=0.3)
              st.plotly_chart(fig_pie_nov, use_container_width=True)
          else:
              st.info("Aucun jeu coché pour le moment.")

      ###########----3. Camembert Catégories (Produits cochés au moins une fois par un utilisateur)
    with col_graph3:
          st.subheader("Jeux cochés par Catégorie")
          if not df_cochis.empty:
              df_cat = df_cochis["categorie"].value_counts().reset_index()
              df_cat.columns = ["Catégorie", "Nombre"]
              fig_pie_cat = px.pie(df_cat, names="Catégorie", values="Nombre", hole=0.3)
              st.plotly_chart(fig_pie_cat, use_container_width=True)
          else:
              st.info("Aucun produit coché pour le moment.")

    st.divider()
    st.caption("Tableau croisé : jeux retenus par l'admin × personnes. Cochez les jeux que vous pouvez prêter.")



    # Configuration du tableau avec AgGrid
    gb = GridOptionsBuilder.from_dataframe(df_jeux)
    gb.configure_default_column(
         resizable=True,
         filterable=True,
         editable=True,
     )
    gb.configure_grid_options(
        wrapHeaderText=True,
        autoHeaderHeight=True,
        rowHeight=60,  # Augmente la hauteur des lignes pour bien voir les images
    )
    image_renderer = JsCode(
        """
        class ImageRenderer {
                init(params) {
                    this.eGui = document.createElement('img');
                    this.eGui.setAttribute('src', params.value);
                    this.eGui.setAttribute('style', 'height: 45px; width: auto; border-radius: 4px; vertical-align: middle;');
                }
                getGui() {
                    return this.eGui;
                }
        }
        """
    )

    gb.configure_column(
        "Aperçu de l'image du produit",
        cellRenderer=image_renderer,
        width=150,
   ) 
    # Applique un thème complet avec bordures
    gridOptions = gb.build()

    AgGrid(
       df_jeux,
       gridOptions=gridOptions,
       theme="balham",  # Thème avec bordures et grille bien visibles
       update_mode=GridUpdateMode.MODEL_CHANGED,
    )

           



           
    # En-tête du tableau
    cols_header = st.columns([2, 1.5,  2 , 3 , 2 , 1 , 1 ] + [1.5] * len(pseudo_list) )

     
    cols_header[0].markdown("nouveaute")
    cols_header[1].markdown("Annee")
    cols_header[2].markdown("Categorie jeu*")
    cols_header[3].markdown("Couverture Jeu")
    cols_header[4].markdown("Jeu")
    cols_header[5].markdown("Total coché par joueur")
    cols_header[6].markdown("Total coché validé par admin")
    for idx, j in enumerate(pseudo_list):
        cols_header[6 + idx].markdown(f"**{j}**  \n*(U / A)*")

    cols_spec = st.columns([2, 1.5,  2 , 3 , 2 , 1 , 1 ] + [3] * len(pseudo_list) )

    cols_spec[0].markdown(" ")
    cols_spec[1].markdown(" ")
    cols_spec[2].markdown(" ")
    cols_header[3].markdown(" ")
    cols_header[4].markdown(" ")
    cols_header[5].markdown(" ")
    cols_header[6].markdown(" ")
    for idx, j in enumerate(pseudo_list):
        cols_header[6 + idx].markdown("Total Validé / Coché")
    
               
    st.divider()  # Séparateur visuel avant la liste des jeux
    #####################-----------------------
    ###################### Lignes du tableau

    for index, row in df_jeux.iterrows():
        cols = st.columns([2, 1.5,  2 , 3 , 2 , 1 , 1 ] + [3] * len(pseudo_list) )
        print(row)

        cols[0].write(row['nouveaute'])
        cols[1].write(row["Annee"])    
        cols[2].write(row["Categorie jeu"])    
        cols[3].write(row["Couverture Jeu"])    
        cols[4].write(row["Jeu"])       
        cols[5].write(row["Total coché par joueur"]) 
        cols[6].write(row["Total coché validé par admin"]) 


               

        # Cellules Joueurs
        for idx, j in enumerate(pseudo_list):
            u_val, a_val = st.session_state.grid_state[(row["Jeu"], j)]

            with cols[6 + idx]:
                # Fond vert si validé par l'admin
                bg_color = "#d4edda" if a_val else "transparent"
                container = st.container()

                with container:
                    st.markdown(
                        f"""
                        <div style="background-color: {bg_color}; padding: 5px; border-radius: 5px; border: 1px solid #ddd;">
                        """,
                        unsafe_allow_html=True,
                    )

                    c1, c2 = st.columns(2)
                    # Checkbox Utilisateur
                    new_u = c1.checkbox(
                        "U",
                        value=u_val,
                        key=f"u_{row["Jeu"]}_{j}",
                        label_visibility="collapsed",
                    )
                    # Checkbox Admin
                    new_a = c2.checkbox(
                        "A",
                        value=a_val,
                        key=f"a_{row["Jeu"]}_{j}",
                        disabled=not is_admin,
                        label_visibility="collapsed",
                    )

                    st.markdown("</div>", unsafe_allow_html=True)

                    # Mise à jour de l'état si modification
                    if new_u != u_val or new_a != a_val:
                        st.session_state.grid_state[(row["Jeu"], j)] = [new_u, new_a]
                        st.rerun()





   
####    pseudo_list = list(u["pseudo"] for u in users)      

####    print(pseudo_list)
####    # Initialisation dans la session
####    if "df" not in st.session_state:
####               df = pd.DataFrame(rows)
####               st.session_state["df"] = df

####    # Configuration dynamique des colonnes du tableau
####    config = {
####        "Couverture Jeu": st.column_config.ImageColumn("Visuel"),
####        "Total coché": st.column_config.NumberColumn("Total coché", disabled=True)
####    }       
####    # Ajout dynamique des nouvelles colonnes si la liste évolue
####    for pseudo in pseudo_list :
####        if  pseudo not in st.session_state["df"].columns:
####            st.session_state["df"][pseudo] = False
####        # Génération automatique des cases à cocher pour chaque personne
####        config[pseudo] = st.column_config.CheckboxColumn( pseudo.capitalize(), default=False)




####    # Affichage du tableau interactif
####    liste_jeux = st.data_editor(
####        st.session_state["df"],
####        column_config=config,
####        use_container_width=True,
####        key="editor"
####    )

####    # Recalcul de la somme basé sur la liste dynamique
####    #liste_jeux["Total coché"] = liste_jeux[pseudo].sum(axis=1)


####    # Création du tableau croisé avec la somme
####    pivot_df = pd.pivot_table(
####       liste_jeux,
####        values=liste_jeux[pseudo],
####        #index=index_col,
####        columns=liste_jeux[pseudo],
####        aggfunc='sum',      # La somme des 1 compte les cases cochées
####        fill_value=0,
####        margins=True,
####        margins_name="Total coché"
####    )       

####    # Synchronisation de la session
####    st.session_state["df"] = liste_jeux       
  
####    st.markdown(
####        """
####        <style>
####        /* Agrandit la hauteur des cellules et conteneurs du tableau */
####        [data-testid="stTable"] td, 
####        div[data-testid="stDataEditor"] div[role="grid"] div[role="row"] {
####            min-height: 100px !important;
####            height: 500px !important;
####        }
####        /* Permet à l'image de prendre toute la hauteur disponible */
####        div[data-testid="stDataEditor"] img {
####            max-height: 5000px !important;
####            object-fit: contain;
####        }
####        </style>
####        """,
####        unsafe_allow_html=True,
####    )

####    st.subheader("📋 Grille de suivi")


        

####    # 5. TABLEAU RÉCAPITULATIF PAR PERSONNE ET TOTAL
####    st.subheader("📊 Récapitulatif des validations")
    
####    totaux_par_personne = liste_jeux[users_list].sum().to_dict()
####    total_general = sum(totaux_par_personne.values())
####    print(totaux_par_personne)
####    # Création du DataFrame récapitulatif
####    df_recap = pd.DataFrame(
####        totaux_par_personne, 
####        columns=["Personne", "Nombre de coches"]
####    )
####    # Affichage avec ligne de Total Général via les metrics ou un tableau
####    col1, col2 = st.columns([2, 1])

####    with col1:
####        st.dataframe(df_recap, hide_index=True, width="stretch")

####    with col2:
####        st.metric(label="🎯 Total Général", value=total_general)
    

####    with button_container:
####        if st.button("Enregistrer les prêts", type="primary"):
####            for r in edited.iterrows():
####                ckey = df.loc[df["Jeu"] == r["Jeu"], "_ckey"].values[0]
####                for u in users:
####                    storage_jeux.set_loan(ckey, u["id"], bool(r[u["pseudo"]]))
####            st.success("Prêts enregistrés")
####            #st.rerun()
      
    
        

