"""Vues / écrans Streamlit."""
import html

import streamlit as st
from  storage_presence import get_presence, clear_user_presence, clear_all_presence, get_all_presence, get_tasks, add_task, update_task, delete_task
import sys
from pathlib import Path
from config_presence import DAYS, PERIODS, PERIOD_LABELS, SLOT_KEYS

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
            auth.logout()
            st.rerun()

    if page == "Ma présence":
        presence_page(user)
    elif page == "Récapitulatif":
        recap_page()
    else:
        admin_page()


def _slot_key(day, period):
    return f"{day}_{period}"


def presence_editor(user_id: str, user_name: str, key_prefix: str):
    """Éditeur de présence réutilisable (soi-même ou, pour l'admin, une autre personne)."""
    data = get_presence(user_id)
    print("creneau")
    print(data )
    print("fin creneau")
    cols = st.columns(2)
    slot_state = {}
    for i, (day, day_label) in enumerate(DAYS):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"#### {day_label}")
                full_key = f"{key_prefix}_full_{day}"
                current_full = all(data["creneau"][_slot_key(day, p)] for p, _ in PERIODS)
                #current_full = all([_slot_key(day, p)] for p, _ in PERIODS)
                
                full = st.checkbox("Journée entière", value=current_full, key=full_key)
                for period, plabel in PERIODS:
                    sk = _slot_key(day, period)
                    default = True if full else data["creneau"][sk]
                    # Si "journée entière" est coché, force les trois créneaux.
                    val = st.checkbox(plabel, value=default, key=f"{key_prefix}_{sk}",
                                      disabled=full)
                    slot_state[sk] = True if full else val

    st.markdown("#### Tâches souhaitées")
    tasks = get_tasks()
    print("liste tache")
    print(tasks)
    print("fin liste tache")
    
    
    selected = []
    if not tasks:
        st.info("Aucune tâche disponible. L'administrateur doit en ajouter.")
    for t in tasks:
        checked = t["_id"] in data["task_ids"]
        if st.checkbox(t["tache"], value=checked, key=f"{key_prefix}_task_{t['_id']}"):
            selected.append(t["_id"])

    return slot_state, selected


def presence_page(user: dict):
    st.title("Ma présence")
    st.caption("Cochez vos créneaux de disponibilité (Samedi & Dimanche) et vos tâches souhaitées.")
    slot_state, selected = presence_editor(user["_id"], user["pseudo"], "self")
    if st.button("Enregistrer", type="primary"):
        set_presence(user["id"], user["pseudo"], slot_state, selected)
        st.success("Présence enregistrée")


def recap_page():
    st.title("Tableau récapitulatif")
    st.caption("Tâches (lignes) × Jours & créneaux (colonnes). Les personnes présentes apparaissent dans chaque cellule.")

    tasks = get_tasks()
    presence = get_all_presence()

    columns = [(f"{d}_{p}", dl, pl) for d, dl in DAYS for p, pl in PERIODS]

    matrix = {t["id"]: {c[0]: [] for c in columns} for t in tasks}
    for p in presence.values():
        name = p.get("user_name", "")
        for tid in p.get("task_ids", []):
            if tid in matrix:
                for sk, active in p.get("creneau", {}).items():
                    if active and sk in matrix[tid]:
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
            names = matrix[t["id"]][c[0]]
            if names:
                cells += "<td>" + "".join(
                    f"<span class='ws-badge'>{html.escape(n)}</span>" for n in names
                ) + "</td>"
            else:
                cells += "<td class='ws-empty'>—</td>"
        body += f"<tr><td>{html.escape(t['label'])}</td>{cells}</tr>"

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
            label = c1.text_input("t", value=t["tache"], key=f"edit_{t['_id']}",
                                   label_visibility="collapsed")
            #  if c2.button("Modifier", key=f"upd_{t['_id']}"):
            if c2.button("Modifier"):
                update_task(t["_id"], label)
                st.rerun()
            # if c3.button("Supprimer"):
            if c3.button("Supprimer"):
                delete_task(t["_id"])
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
