"""Vues / écrans Streamlit."""
import html

import streamlit as st
from  storage_presence import get_presence, clear_user_presence, clear_all_presence, get_all_presence, get_tasks, add_task, update_task, delete_task, set_presence
import sys
from pathlib import Path
from config_presence import DAYS, PERIODS, PERIOD_LABELS, SLOT_KEYS, DAYS_INSTALL, PERIODS_INSTALL,TYPE_TASK_INSTALL , TYPE_TASK_ANIMATION ,DAYS_ANIMATION , PERIODS_ANIMATION ,PERIODS_ENTIERE, SLOT_KEYS_INSTALL ,SLOT_KEYS_ANIMATION

# Ajoute le dossier parent (la racine du projet) à sys.path
racine_projet = Path(__file__).resolve().parent.parent
sys.path.append(str(racine_projet))

import commun.auth


# ==========================================================================
# APPLICATION PRINCIPALE
# ==========================================================================
def main_app(user: dict):
    with st.sidebar:
        st.markdown("### 📅 Week-end")
        st.write(f"**{user['pseudo']}**")
        st.caption(user["email"])
        if user["role"] == "admin":
            st.markdown("<span class='ws-tag-admin'>Admin</span>", unsafe_allow_html=True)

        pages = ["Ma présence", "Récapitulatif"]
        if user["role"] == "admin":
            pages.append("Administration")
        page = st.radio("Navigation", pages, label_visibility="collapsed")

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

    creneau_selc = get_presence(user_id)

    # Récupération des présences existantes en BDD pour initialiser si besoin
    periode_db = set()
    taches_db = set()
    for lstcre in creneau_selc:
        for creneaux in lstcre.get("creneau", []):
            periode_db.add(creneaux[0])  # ex: 'samedi_matin'
            taches_db.add(str(creneaux[1]))  # ID tâche en string

    cols = st.columns(3)

    for i, (day, day_label) in enumerate(DAYS):

        # Détermination du type de jour
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

        # Affichage dans la colonne
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"#### {day_label}")

                # Gestion checkbox "Journée entière"
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

                # Checkboxes des périodes
                for period, plabel in Periods:
                    pkey = f"{key_prefix}_period_{day}_{period}"

                    # Initialisation depuis la BDD uniquement au 1er chargement
                    if pkey not in st.session_state:
                        st.session_state[pkey] = (
                            f"{day}_{period}" in periode_db
                        )

                    is_disabled = st.session_state.get(
                        f"{key_prefix}_full_{day}", False
                    )
                    st.checkbox(plabel, key=pkey, disabled=is_disabled)

                st.markdown(
                    "<hr style='border-top: 3px solid #FF4B4B; margin: 15px 0;'>",
                    unsafe_allow_html=True,
                )
                st.markdown("#### Tâches souhaitées")

                if not tasks:
                    st.info("Aucune tâche disponible.")

                for t in tasks:
                    t_id = str(t["_id"])
                    tkey = f"{key_prefix}_task_{day}_{t_id}"

                    # Initialisation BDD
                    if tkey not in st.session_state:
                        st.session_state[tkey] = t_id in taches_db

                    st.checkbox(t["tache"], key=tkey)

    # --- RÉCUPÉRATION DES SÉLECTIONS ---
    selected = []

    # 1. Récupère toutes les périodes cochées
    # Clé type: 'self_period_samedi_matin' -> découpe à partir de 'period_'
    list_period_coche = [
        key.split(f"{key_prefix}_period_")[1]
        for key in st.session_state
        if key.startswith(f"{key_prefix}_period_") and st.session_state[key]
    ]

    # 2. Récupère toutes les tâches cochées
    # Clé type: 'self_task_samedi_6a8ea959...' -> extrait l'ID après le dernier '_'
    list_task_coche = [
        key.split("_")[-1]
        for key in st.session_state
        if key.startswith(f"{key_prefix}_task_") and st.session_state[key]
    ]

    # Croisement des résultats
    for period in list_period_coche:
        for task in list_task_coche:
            selected.append([period, task])

    return selected


def presence_page(user: dict):
    st.title("Ma présence")
    st.caption("Cochez vos créneaux de disponibilité et vos tâches souhaitées.")
 
    selected = presence_editor(user["id"], user["pseudo"], "self")

    if st.button("Enregistrer", type="primary"):
        set_presence(user["id"], user["pseudo"],  selected)
        st.success("Présence enregistrée")


def recap_page():
    st.title("Tableau récapitulatif")
    st.caption("Tâches (lignes) × Jours & créneaux (colonnes). Les personnes présentes apparaissent dans chaque cellule.")

    tasks = get_tasks("all")
    print("TACHE")
    print(tasks)
    presence = get_all_presence()
    print("presence")
    print(presence)



    columns = [(f"{d}_{p}", dl, pl) for d, dl in DAYS for p, pl in PERIODS]
  
    matrix = {str(t["_id"]): {c[0]: [] for c in columns} for t in tasks}
    for p in presence :
        name = p["pseudo"]
        for tid in p["task_ids"]:
            if str(tid) in matrix:
                for sk, statut in p["creneau"].items() :
                    if statut:
                        if  sk in matrix[tid]:
                            matrix[tid][sk].append(name)
    print("matrix")
    print(matrix)
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
        st.subheader("Liste des tâches")
        with st.form("add_task_form", clear_on_submit=True):
            c1, c2 = st.columns([4, 1])
            new_label = c1.text_input("Nouvelle tâche", label_visibility="collapsed",
                                      placeholder="Nom de la nouvelle tâche")
            if c2.form_submit_button("Ajouter", type="primary") and new_label.strip():
                add_task(new_label)
                st.rerun()

        for t in get_tasks():
            c1, c2, c3 = st.columns([4, 1, 1])
            label = c1.text_input("t", value=t["tache"], key=f"edit_{t['id']}",
                                   label_visibility="collapsed")
            #  if c2.button("Modifier", key=f"upd_{t['id']}"):
            if c2.button("Modifier"):
                update_task(t["id"], label)
                st.rerun()
            # if c3.button("Supprimer"):
            if c3.button("Supprimer"):
                delete_task(t["id"])
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
        users = [u for u in get_users()]
        if not users:
            st.info("Aucun utilisateur.")
            return
        options = {f"{u['pseudo']} ({u['email']})": u for u in users}
        choice = st.selectbox("Personne", list(options.keys()))
        target = options[choice]

        if st.button(f"Réinitialiser les votes de {target['pseudo']}"):
            clear_user_presence(target["id"])
            st.success(f"Votes de {target['pseudo']} réinitialisés")
            st.rerun()

        st.markdown("**Modifier les votes de cette personne :**")
        slot_state, selected = presence_editor(target["id"], target["pseudo"], f"admin_{target['id']}")
        if st.button("Enregistrer les votes de cette personne", type="primary"):
            set_presence(target["id"], target["pseudo"], slot_state, selected)
            st.success(f"Votes de {target['pseudo']} enregistrés")
