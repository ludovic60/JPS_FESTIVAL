"""Vues / écrans Streamlit."""
import html

import streamlit as st
from  storage_presence import get_presence, clear_user_presence, clear_all_presence, get_all_presence, get_tasks, add_task, update_task, delete_task, set_presence
import sys
from pathlib import Path
from config_presence import DAYS, PERIODS, PERIOD_LABELS, SLOT_KEYS, DAYS_INSTALL, PERIODS_INSTALL,TYPE_TASK_INSTALL , TYPE_TASK_ANIMATION ,DAYS_ANIMATION , PERIODS_ANIMATION ,PERIODS_ENTIERE, SLOT_KEYS_INSTALL ,SLOT_KEYS_ANIMATION, LIST_TYPE_TASK
import time 

# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))

import commun.auth
import commun.common_store

def on_page_change():
    """Déclenché automatiquement dès que l'utilisateur change de page dans la sidebar."""
    # Si on quitte ou revient sur "Ma présence", on nettoie le cache BDD et les checkboxes
    bdd_key = f"db_loaded_self_{st.session_state.get('user_id_current', '')}"

    if bdd_key in st.session_state:
        del st.session_state[bdd_key]

    # Supprime toutes les clés associées aux checkboxes de présence
    keys_to_clear = [k for k in st.session_state if k.startswith("self_")]
    for k in keys_to_clear:
        del st.session_state[k]

# ==========================================================================
# APPLICATION PRINCIPALE
# ==========================================================================
def main_app(user: dict):
    st.session_state["user_id_current"] = user["id"]
    with st.sidebar:
        st.markdown("### 📅 Week-end")
        st.write(f"**{user['pseudo']}**")
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)

        pages = ["Ma présence", "Récapitulatif"]
        if user["role"] == "admin":
            pages.append("Administration")
        page = st.radio("Navigation", pages, label_visibility="collapsed", on_change=on_page_change)

        st.divider()
        if st.button("Déconnexion"):
            commun.auth.logout()
            st.rerun()

    if page == "Ma présence":
        presence_page(user)

    elif page == "Récapitulatif":
        recap_page()
    else:
        admin_page()





def presence_editor(user_id: str, user_name: str, key_prefix: str):
    """Éditeur de présence réutilisable."""

    # 1. CHARGEMENT INITIAL (Exécuté une seule fois par session utilisateur)
    bdd_key = f"db_loaded_{key_prefix}_{user_id}"

    if bdd_key not in st.session_state:
        creneau_selc = get_presence(user_id)
        periode_db = set()
        taches_db = set()

        for lstcre in creneau_selc:
            for creneaux in lstcre.get("creneau", []):
                periode_db.add(creneaux[0])  # ex: 'samedi_matin'
                taches_db.add(f"{str(creneaux[1])}_{str(creneaux[0]).split("_")[0]}")  # ID tâche

        st.session_state[bdd_key] = {"periodes": periode_db, "taches": taches_db}

    initial_periodes = st.session_state[bdd_key]["periodes"]
    initial_taches = st.session_state[bdd_key]["taches"]

    cols = st.columns(3)

    for i, (day, day_label) in enumerate(DAYS):

        Periods = []
        tasks = []
        for j, _ in DAYS_INSTALL:
            if day == j:
                Periods = PERIODS_INSTALL
                tasks = get_tasks(TYPE_TASK_INSTALL)

        for j, _ in DAYS_ANIMATION:
            if day == j:
                Periods = PERIODS_ANIMATION
                tasks = get_tasks(TYPE_TASK_ANIMATION)

        with cols[i]:
            with st.container(border=True):
                st.markdown(f"#### {day_label}")

                # Callback Journée Entière
                def on_full_change(d=day, p_list=Periods):
                    new_val = st.session_state[f"{key_prefix}_full_{d}"]
                    for pk, _ in p_list:
                        st.session_state[
                            f"{key_prefix}_period_{d}_{pk}"
                        ] = new_val

                if len(Periods) == PERIODS_ENTIERE:
                    full_key = f"{key_prefix}_full_{day}"
                    st.checkbox(
                        "Journée entière", key=full_key, on_change=on_full_change
                    )

                # --- CHECKBOXES PÉRIODES ---
                for period, plabel in Periods:
                    pkey = f"{key_prefix}_period_{day}_{period}"

                    # Si la clé n'existe pas encore dans session_state, on l'initialise
                    if pkey not in st.session_state:
                        st.session_state[pkey] = (
                            f"{day}_{period}" in initial_periodes
                        )

                    is_disabled = st.session_state.get(
                        f"{key_prefix}_full_{day}", False
                    )

                    # ON NE PASSE PLUS value= ICI
                    st.checkbox(plabel, key=pkey, disabled=is_disabled)

                st.markdown(
                    "<hr style='border-top: 3px solid #FF4B4B; margin: 15px 0;'>",
                    unsafe_allow_html=True,
                )
                st.markdown("#### Tâches souhaitées")

                if not tasks:
                    st.info("Aucune tâche disponible.")

                # --- CHECKBOXES TÂCHES ---
                for t in tasks:
                    t_id = str(t["_id"])
                    tkey = f"{key_prefix}_task_{day}_{t_id}"

                    # Si la clé n'existe pas encore dans session_state, on l'initialise
                    if tkey not in st.session_state:
                        tache_coche = ([item.split("_")[0] for item in initial_taches if item.split("_")[1] == day and item.split("_")[0] == t_id])
                                              
                        if tache_coche :
                            st.session_state[tkey] = tache_coche[0] ==tache_coche[0]

                    # ON NE PASSE PLUS value= ICI
                    st.checkbox(t["tache"], key=tkey)

    # --- SÉLECTION FINALE ---
    selected = []

    # Récupère toutes les périodes cochées : ['samedi_matin', 'dimanche_apres_midi', ...]
    periodes_cochees = [
        key.replace(f"{key_prefix}_period_", "")
        for key in st.session_state
        if key.startswith(f"{key_prefix}_period_") and st.session_state[key]
    ]

    # Récupère les tâches cochées par jour : { 'samedi': ['id_tache1', 'id_tache2'], ... }
    taches_par_jour = {}
    for key in st.session_state:
        if key.startswith(f"{key_prefix}_task_") and st.session_state[key]:
            # Exemple de clé: 'self_task_samedi_6a8ea959d094f4012f19dfa9'
            parts = key.split("_")
            jour = parts[2]
            tache_id = parts[3]

            if jour not in taches_par_jour:
                taches_par_jour[jour] = []
            taches_par_jour[jour].append(tache_id)

    # Association période <-> tâche du même jour
    for period in periodes_cochees:
        jour_du_creneau = period.split("_")[0]  # ex: 'samedi'
        taches_du_jour = taches_par_jour.get(jour_du_creneau, [])

        for t_id in taches_du_jour:
            selected.append([period, t_id])

    return selected



def presence_page(user: dict):
    st.title("Ma présence")
    st.caption("Cochez vos créneaux de disponibilité et vos tâches souhaitées.")

    selected = presence_editor(user["id"], user["pseudo"], "self")

    if st.button("Enregistrer", type="primary"):
        
        set_presence(user["id"], user["pseudo"], selected)
        st.success("Présence enregistrée")



############### page de recap de toutes les presences 
def recap_page():
    st.title("Tableau récapitulatif")
    st.caption("Tâches (lignes) × Jours & créneaux (colonnes). Les personnes présentes apparaissent dans chaque cellule.")

    tasks = get_tasks("all")

    presence = get_all_presence()




    columns = [(f"{d}_{p}", dl, pl) for d, dl in DAYS_INSTALL for p, pl in PERIODS_INSTALL]+[(f"{d}_{p}", dl, pl) for d, dl in DAYS_ANIMATION for p, pl in PERIODS_ANIMATION]
  
    matrix = {str(t["_id"]): {c[0]: [] for c in columns} for t in tasks}
    for p in presence :
        name = p["pseudo"]
        for sk , tid in p["creneau"]:
            if str(tid) in matrix:
                if  sk in matrix[tid]:
                    matrix[tid][sk].append(name)
   
    head = "<tr><th>Tâche</th>" + "".join(
        f"<th>{c[1]}<br><span style='font-weight:400;font-size:11px;opacity:.7'>{c[2]}</span></th>"
        for c in columns
    ) + "</tr>"

    body = ""


    if not tasks:
        body = f"<tr><td colspan='{len(columns)+1}'>Aucune tâche définie.</td></tr>"
    for t in tasks:
        cells = ""
        for c in columns:
            names = matrix[str(t["_id"])][c[0]]
            if names:
                cells += "<td>" + "".join(
                    f"<span class='ws-badge'>{html.escape(n)}</span>" for n in names
                ) + "</td>"
            else:
                cells += "<td class='ws-empty'>—</td>"
        body += f"<tr><td>{html.escape(t['tache'])}</td>{cells}</tr>"

    st.markdown(f"<table class='ws-recap'><thead>{head}</thead><tbody>{body}</tbody></table>",
                unsafe_allow_html=True)
    st.caption("Une personne apparaît dans une cellule si elle est présente sur ce créneau ET a choisi cette tâche.")


def admin_page():
    st.title("Administration")
    tab_tasks, tab_votes = st.tabs(["Gestion des tâches", "Gestion des votes"])

    # ---- Tâches ----
    with tab_tasks:

        choice = st.selectbox("type de tache ", list(LIST_TYPE_TASK))
        st.subheader("Liste des tâches")
        with st.form("add_task_form", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            new_label = c1.text_input("Nouvelle tâche", label_visibility="collapsed",
                                      placeholder="Nom de la nouvelle tâche")
            if c2.form_submit_button("Ajouter", type="primary") and new_label.strip():
                add_task(new_label,choice)
                st.rerun()

        for t in get_tasks("all"):
            c1, c2, c3 = st.columns([4, 1, 1])
            label = c1.text_input("t", value=t["tache"], key=f"edit_{t["_id"]}",
                                   label_visibility="collapsed")
            
            if c2.button("Modifier", key=f"modif_{t["_id"]}"):
                update_task(t["_id"], label, choice)
                print(t["_id"])
                st.rerun()
            # if c3.button("Supprimer"):
            if c3.button("Supprimer", key=f"supprim_{t["_id"]}"):
                delete_task(t["_id"])
                print(t["_id"])
                st.rerun()

    # ---- Votes ----
    with tab_votes:
        st.subheader("Réinitialiser tous les votes")
        st.caption("Efface les présences et tâches choisies de TOUTES les personnes.")
        if st.button("Réinitialiser tous les votes", type="primary"):
            st.session_state["confirm_reset_all"] = True
        if st.session_state.get("confirm_reset_all"):
            st.warning("Confirmer la suppression de tous les votes ?")
            c1, c2 = st.columns(2)
            if c1.button("Oui, tout réinitialiser"):
                clear_all_presence()
                st.session_state.pop("confirm_reset_all", None)
                st.success("Tous les votes ont été réinitialisés")
            if c2.button("Annuler"):
                st.session_state.pop("confirm_reset_all", None)

        st.divider()
        st.subheader("Modifier / réinitialiser les votes d'une personne")
        users = [u for u in commun.common_store.get_users()]
        print(users)
        if not users:
            st.info("Aucun utilisateur.")
            return
        options = {f"({u["pseudo"]}) ({u["email"]})" for u in users}
       
        
        choice = st.selectbox("Personne", list(options))
    
        target = [
            u
            for u in users
            if f"{u['pseudo']} ({u['email']})" == choice  # Comparaison directe avec le format du selectbox
        ]    

        print("target")
        print(target)
                
        if st.button(f"Réinitialiser les votes de {target[0]["pseudo"]}"):
            clear_user_presence(target[0]["_id"])
            st.success(f"Votes de {target[0]['pseudo']} réinitialisés")
            st.rerun()

        st.markdown("**Modifier les votes de cette personne :**")
        selected = presence_editor(target[0]["_id"], target[0]["pseudo"], f"admin_{target[0]["_id"]}")
        if st.button("Enregistrer les votes de cette personne", type="primary"):
            set_presence(target[0]["_id"], target[0]["pseudo"], selected)
            st.success(f"Votes de {target[0]["pseudo"]} enregistrés")
