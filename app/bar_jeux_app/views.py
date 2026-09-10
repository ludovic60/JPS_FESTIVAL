"""Vues Streamlit pour Bar à jeux."""
 

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode , DataReturnMode , AgGridTheme       
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
from config_game_card import _game_card , mise_forme_categorie , nouveaute_def
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

############################################################################################################
###-------------- page pour generer les mots de passe des user
############################################################################################################


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


############################################################################################################
###-------------- page affichant les jeux 
############################################################################################################


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
  
############################################################################################################
###-------------- page des suggestion et remarque des joueur
############################################################################################################
   
def _requests_suggestion_page(user):
    st.title("liste des suggestions par les joueurs")

    st.markdown("🚧  en cours de construction ")

############################################################################################################
###-------------- page des demandes d'ajout 
############################################################################################################


def _requests_page(user):
    st.title("Demandes d'ajout de jeux")
    reqs = storage_jeux.get_requests("ajout jeux")
    if not reqs:
        st.info("Aucune demande.")
    else :
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
     st.title("liste des remarques par les joueurs")
    st.markdown("🚧  en cours de construction ")
############################################################################################################
###-------------- page où est affiché les jeux selectionné
############################################################################################################

def _final_page(user):
    st.title("Liste finale — Prêts")



    # --- EXTRACTION DES DONNEES UTILES ---
        #--- liste des jeux
    finals = storage_jeux.final_games()
   
   
    users = cs.get_users_loaner()

    current_user = user
    is_admin = current_user == "admin"
    

    pseudo_list = list(u["pseudo"] for u in users)

           
    # emplacement reservé pour le bouton de validation du pret par les utilisateurs
    if not finals:
        st.info("Aucun jeu retenu par l'admin pour l'instant.")
        return           
    
       

   
    # --- PARTIE SUPERIEURE : GRAPHIQUES ---

    col_graph1, col_graph2, col_graph3 = st.columns(3)

    ###########---- 0 dataframe pour alimenter les graph 

    liste_pret_validé = storage_jeux.get_validated_loans()
    liste_info_valide = []
    for game in  liste_pret_validé :
        id_jeu = game["id_jeux"]
        info_games = storage_jeux.get_info_games(id_jeu)
        # Récupération sécurisée du pseudo (converti en str pour être sûr que les ID matchent)
        user_id_str = str(game_pret["user_id"])
        pseudo = users_dict.get(user_id_str, "Utilisateur inconnu")
       
          
        liste_info_valide.append ({"classement":  info_games_pret[0]["classement_jps_final"] ,  "Nouveauté":nouveaute_def(game["id_jeux"]), "pseudo":pseudo , "nom": info_games[0]["nom_jeu_complet"],"Nb_jeux_valide":1, "statut_valide":True})
     
    df_jeux_valide_graphique  = pd.DataFrame(liste_info_valide)
    liste_info = []
    liste_pret_user = storage_jeux.get_all_loans()
    
    # 1. Optimisation : création d'un dictionnaire d'utilisateurs {str(id): pseudo}
    users_dict = {str(u["_id"]): u.get("pseudo", "Inconnu") for u in users}
    
    for game_pret in liste_pret_user:
   
        # Récupération des infos du jeu
        id_jeu = game_pret["id_jeux"]
        info_games_pret = storage_jeux.get_info_games(id_jeu)
  
        # Récupération sécurisée du pseudo (converti en str pour être sûr que les ID matchent)
        user_id_str = str(game_pret["user_id"])
        pseudo = users_dict.get(user_id_str, "Utilisateur inconnu")
    
        # Ajout à la liste
        liste_info.append({
            "classement": info_games_pret[0]["classement_jps_final"],
            "Nouveauté": nouveaute_def(id_jeu),
            "pseudo": pseudo,
            "nom": info_games_pret[0]["nom_jeu_complet"],
            "Nb_jeux_prete": 1,
        })
    df_jeux_pret_graphique  = pd.DataFrame(liste_info)

 

    ###########---- 1. Histogramme par joueur (Validés vs Cochés Utilisateur)

    with col_graph1:
           
          st.subheader("Validations par Joueur")
          ###----- df_jeux_histogramme  = pd.merge(df_jeux_pret_graphique, df_jeux_valide_graphique, on =["classement", "Nouveauté", "pseudo","nom" ]  , how="left")
          df_jeux_histogramme  = df_jeux_pret_graphique

    
          fig_hist = px.bar(
              df_jeux_histogramme,
              x="pseudo",
              y="Nb_jeux_prete", ###["Nb_jeux_prete","Nb_jeux_valide"]
            #  color="Nb_jeux_prete", ###["Nb_jeux_prete","Nb_jeux_valide"]
              barmode="group",
              #color_discrete_map={"Nb_jeux_prete": "#636EFA"}, ###{"Nb_jeux_prete": "#636EFA", "Nb_jeux_valide": "#2CA02C"},
              width=1000,
              height=500
          )
          st.plotly_chart(fig_hist, use_container_width=True)

    ###########----2. Camembert Nouveautés (jeux cochés au moins une fois par un utilisateur)
    with col_graph2:
          st.subheader("Jeux cochés par Nouveauté")
         
          if not df_jeux_pret_graphique.empty:
              df_nov = df_jeux_pret_graphique["Nouveauté"].value_counts().reset_index()
              df_nov.columns = ["Nouveauté", "Nombre"]
              fig_pie_nov = px.pie(df_nov, names="Nouveauté", values="Nombre", hole=0.3 )
              fig_pie_nov.update_layout(height=250 , width=1000)
              st.plotly_chart(fig_pie_nov, use_container_width=True)
          else:
              st.info("Aucun jeu coché pour le moment.")

          st.subheader("Jeux validés par Nouveauté")
          
          if not df_jeux_valide_graphique.empty:
              df_nov2 = df_jeux_valide_graphique["Nouveauté"].value_counts().reset_index()
              df_nov2.columns = ["Nouveauté", "Nombre"]
              fig_pie_nov2 = px.pie(df_nov2, names="Nouveauté", values="Nombre", hole=0.3 )
              fig_pie_nov2.update_layout(height=250 , width=1000)
              st.plotly_chart(fig_pie_nov2, use_container_width=True)
          else:
              st.info("Aucun jeu validé pour le moment.")

 

      ###########----3. Camembert Catégories (Produits cochés au moins une fois par un utilisateur)
    with col_graph3:
          st.subheader("Jeux cochés par Classement")
          if not df_jeux_pret_graphique.empty:
              df_cat = df_jeux_pret_graphique["classement"].value_counts().reset_index()
              df_cat.columns = ["classement", "Nombre"]
              fig_pie_cat = px.pie(df_cat, names="classement", values="Nombre", hole=0.3  )
              fig_pie_cat.update_layout(height=250 , width=1000) 
              st.plotly_chart(fig_pie_cat, use_container_width=True)
          else:
              st.info("Aucun jeu coché pour le moment.")


          st.subheader("Jeux validés par Classement")
          if not df_jeux_valide_graphique.empty:
              df_cat2 = df_jeux_valide_graphique["classement"].value_counts().reset_index()
              df_cat2.columns = ["classement", "Nombre"]
              fig_pie_cat2 = px.pie(df_cat2, names="classement", values="Nombre", hole=0.3  )
              fig_pie_cat2.update_layout(height=250 , width=1000) 
              st.plotly_chart(fig_pie_cat2, use_container_width=True)
          else:
              st.info("Aucun jeu validé pour le moment.")

    st.divider()
    st.caption("Tableau croisé : jeux retenus par l'admin × personnes. Cochez les jeux que vous pouvez prêter.")


    ###################################################################################################
    ###########  gestion du tableau des prêts   
    ###################################################################################################
    # creation des lignes du futur tableau croisé         
    row_jeux = []
    ##-------------------------------------------------
    #####--- fonction pour retrouver les infos en base
    ##-------------------------------------------------
    liste_jeu_plusieurs_exemplaire= storage_jeux.final_games_statut_plusieurs_exemplaire()
    print(liste_jeu_plusieurs_exemplaire)
    def get_game_several_selected(game_id):
        result = False 
        
        for id in liste_jeu_plusieurs_exemplaire :
          if game_id== id :
            print(f"passage boucle vrai {game_id}  et {result}") 
            result = True
          else :
            print(f"result plusieurs exemplaires {game_id}  et {result}")
            result = False 

        print(f"result plusieurs exemplaires {game_id}  et {result}")
        return result


    list_jeu_prete = storage_jeux.get_all_loans()
    list_jeu_prete_valide =  storage_jeux.get_validated_loans()


    def get_prete_value(game_id, player_key):
        result = False 
        for pret in list_jeu_prete :
          if game_id== pret["id_jeux"] and player_key== pret["user_id"]:
            result = True
          else :
            result = False 
        print(f"result prete {game_id}  et {result}")   
        return result
    
    def get_admin_valide_value(game_id, player_key):
        result = False 
        for pret in list_jeu_prete_valide :
          if game_id== pret["id_jeux"] and player_key== pret["user_id"]:
            result = True
          else :
            result = False 
          print(f"result valide {game_id}  et {result}")     
        return result

    ##-------------------------------------------------
    #####--- fonction pour mettre les infos en base 
    ##-------------------------------------------------
    def on_change_prete(game_id, player_key, new_val) :
       print(f"change prete afaire {game_id}   {player_key}   {new_val}  ")  
       storage_jeux.toggle_loan(game_id, player_key, new_val)
       print("change prete done")  
     
    def on_change_admin(game_id, player_key, new_val) :
       storage_jeux.set_loan_valide_admin(game_id, player_key, new_val)           
                        
    def on_change_plusieurs_exemplaires(game_id, new_val) :
        print(f"change plusieur exempl afaire {game_id}   {new_val}  ")  
        storage_jeux.toggle_admin_selected(game_id, new_val)
        print("changeplusieurs exempalire")                 


    ##-------------------------------------------------
    #####--- le tableau
    ##-------------------------------------------------
    for game in finals:
        g = storage_jeux.get_info_games(game.get('id_jeux'))
        game_id = str(g[0].get("_id"))
    
        # ... calcul de New (nouveauté) 

        ######   gestion du staut de nouveauté
        New = nouveaute_def(game_id)
  
    
        row = {
            "_id": game_id,                                  
            "nouveaute": New,
            "Annee": g[0].get("annee_parution"),
            "Categorie jeu": mise_forme_categorie(g[0].get("classement_jps_final")),
            "Couverture Jeu": g[0].get("couverture"),
            "Jeu": g[0].get("nom_jeu_complet"),
            "Plusieurs exemplaires souhaités": bool(get_game_several_selected(game_id)),  # <-- vrai bool
            "Total coché par joueur": "",
            "Total coché validé par admin": "",
        }
    
        for idx, j in enumerate(pseudo_list):
            player_key = f"j{idx+1}"
            row[f"{player_key}_prete"] = bool(get_prete_value(game_id, player_key))  # <-- vrai bool
            row[f"{player_key}_admin"] = bool(get_admin_valide_value(game_id, player_key))  # <-- vrai bool
    
        row_jeux.append(row)
    
    df_jeux = pd.DataFrame(row_jeux)

    # --- Colonnes ---
    # --- Colonnes simples (non groupées) ---
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

    gb = GridOptionsBuilder.from_dataframe(
        df_jeux[["nouveaute", "Annee", "Categorie jeu", "Couverture Jeu", "Jeu",
                 "Plusieurs exemplaires souhaités",
                 "Total coché par joueur", "Total coché validé par admin"]]
    )
    gb.configure_column("_id", hide=True)
#    gb.configure_default_column(  width=140)
    gb.configure_column(
        "nouveaute",
        editable=False,
        width=80,
        minWidth=80,
        maxWidth=80,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )

    gb.configure_column(
        "Annee",
        editable=False,
        width=80,
        minWidth=80,
        maxWidth=80,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )
    gb.configure_column(
        "Categorie jeu",
        editable=False,
        width=180,
        minWidth=180,
        maxWidth=180,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )
    gb.configure_column(
        "Couverture Jeu",
        editable=False,
        cellRenderer=image_renderer,
        width=100,
        minWidth=100,
        maxWidth=100,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )
    gb.configure_column(
        "Jeu",
        editable=False,
        width=150,
        minWidth=100,
        maxWidth=150,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True, 
    )

    gb.configure_column(
        "Plusieurs exemplaires souhaités",
        editable=True,
        cellRenderer="agCheckboxCellRenderer",
        width=90,
        minWidth=30,
        maxWidth=90,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )

    gb.configure_column(
        "Total coché par joueur",
        editable=False,
        width=80,
        minWidth=80,
        maxWidth=80,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )
    gb.configure_column(
        "Total coché validé par admin",
        editable=False,
        width=90,
        minWidth=90,
        maxWidth=90,
        suppressSizeToFit=True,
        wrapHeaderText=True, 
        autoHeaderHeight=True,
    )

   
    gb.configure_grid_options(singleClickEdit=True , rowHeight=60)
    
    grid_options = gb.build()



    
    # --- Colonnes groupées par joueur (double en-tête) ---
    for idx, j in enumerate(pseudo_list):
        player_key = f"j{idx+1}"
        group_col = {
            "headerName": j,                      # 1er niveau d'en-tête : le pseudo
            "children": [
                {
                    "field": f"{player_key}_prete",
                    "headerName": "Je prête",      # 2e niveau d'en-tête
                    "editable": True,
                    "cellRenderer": "agCheckboxCellRenderer",
                    "width": 110,
                    "suppressSizeToFit": True,
                },
                {
                    "field": f"{player_key}_admin",
                    "headerName": "Validé",
                    "editable": (user["role"] == "admin"),
                    "cellRenderer": "agCheckboxCellRenderer",
                    "width": 110,
                    "suppressSizeToFit": True,
                    "cellStyle": JsCode("""
                        function(params) {
                            if (params.value === true) {
                                return {backgroundColor: '#d4edda', color: '#155724'};
                            }
                            return null;
                        }
                    """),
                },
            ],
        }
        grid_options["columnDefs"].append(group_col)



    ###### mise en forme du tableau 


    # Hauteur d'en-tête un peu plus grande pour laisser la place aux 2 lignes
    grid_options["groupHeaderHeight"] = 20
    grid_options["headerHeight"] = 20
   # --- Calcul de la hauteur dynamique ---
    header_height = 40     # Hauteur totale de l'en-tête (40px groupHeader + 40px header)
    row_height =70         # Hauteur estimée d'une ligne
    padding = 20            # Marge de sécurité
    
    # Calcul basé sur le nombre de lignes dans df_jeux
    dynamic_height = header_height + (len(df_jeux) * row_height) + padding
    
    # Optionnel : appliquer des limites min/max pour éviter les extrêmes
    dynamic_height = min(max(dynamic_height, 200), 800)  # Entre 200px et 800px max


    st.markdown("""
        <style>
        /* Bordures verticales (colonnes) */
        .ag-theme-streamlit .ag-cell, 
        .ag-theme-streamlit .ag-header-cell,
        .ag-theme-alpine .ag-cell, 
        .ag-theme-alpine .ag-header-cell {
            border-right: 1px solid #d0d0d0 !important;
        }

        /* Bordures horizontales (lignes) */
        .ag-theme-streamlit .ag-row,
        .ag-theme-alpine .ag-row {
            border-bottom: 1px solid #d0d0d0 !important;
        }

        /* Bordure inférieure pour les en-têtes */
        .ag-theme-streamlit .ag-header,
        .ag-theme-alpine .ag-header {
            border-bottom: 2px solid #b0b0b0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    grid_response = AgGrid(
        df_jeux,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        data_return_mode=DataReturnMode.AS_INPUT,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False,
        height=dynamic_height
    )
    
    new_df = pd.DataFrame(grid_response["data"])   # 
    
    # --- Détection des changements ---
    old_df = st.session_state.get("old_grid_df")
    
    if old_df is not None and len(old_df) == len(new_df):
        checkbox_cols = [
            c for c in new_df.columns
            if c.endswith(("prete", "_admin")) or c == "Plusieurs exemplaires souhaités"
        ]
        for i in new_df.index:
            game_id = new_df.at[i, "_id"]
            print(f"game id  {game_id}")
            for col in checkbox_cols:
                old_val = old_df.at[i, col]
                new_val = new_df.at[i, col]
                if bool(old_val) != bool(new_val):
                    print(f"col  {col}")
                    if col.endswith("_prete"):
                        player_key = col.replace("_prete", "")
                        on_change_prete(game_id, player_key, new_val)
                    elif col.endswith("_admin"):
                        player_key = col.replace("_admin", "")
                        on_change_admin(game_id, player_key, new_val)
                    elif col == "Plusieurs exemplaires souhaités":
                        print("appel fonction changement exemplaire")
                        on_change_plusieurs_exemplaires(game_id, new_val)
    
    st.session_state["old_grid_df"] = new_df.copy()
