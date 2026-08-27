"""Stockage App2 (Bar à jeux) — utilisateurs & données mutables partagés via common_store.
Les listes de jeux restent des fichiers plats JSON nommés par mois (exigence)."""
import json
import uuid
from datetime import datetime, timezone
from threading import Lock
import config_bar_jeux

import os
import sys
# Ajoute le dossier parent à sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import commun.common_store as cs
from commun.security import hash_password, verify_password
import commun.config as ccfg

_lock = Lock()

_COVERS = [
    "https://images.unsplash.com/photo-1769288361029-187caa2a88a3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1637120149073-54319e6f9fc3?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.unsplash.com/photo-1772380405894-51b9728ecb88?crop=entropy&cs=srgb&fm=jpg&q=85&w=400",
    "https://images.pexels.com/photos/31916806/pexels-photo-31916806.jpeg?auto=compress&cs=tinysrgb&w=400",
]





# ---- Jeux (fichiers plats) ----
def load_games(list_key):
    games = _read(config_bar_jeux.games_file(list_key), [])
    for g in games:
        if "id" not in g:
            g["id"] = g.get("id_myludo") or uuid.uuid4().hex[:8]
    return games



# ---- Sélection admin / suggestions / demandes / prêts (partagés) ----
def get_admin_selected():
    return set(cs.get_doc("jeux_admin_selected", []))


def toggle_admin_selected(ckey, value):
    sel = get_admin_selected()
    sel.add(ckey) if value else sel.discard(ckey)
    cs.put_doc("jeux_admin_selected", sorted(sel))


def get_suggestions():
    return cs.get_doc("jeux_suggestions", {})


def toggle_suggestion(ckey, user_id, value):
    s = get_suggestions()
    lst = set(s.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    s[ckey] = sorted(lst)
    cs.put_doc("jeux_suggestions", s)


def get_requests():
    return cs.get_doc("jeux_requests", [])


def add_request(name, myludo_url, list_key, by_name):
    reqs = get_requests()
    reqs.append({"id": uuid.uuid4().hex[:8], "name": name.strip(), "myludo_url": myludo_url.strip(),
                 "list_key": list_key, "by": by_name, "created_at": datetime.now(timezone.utc).isoformat()})
    cs.put_doc("jeux_requests", reqs)


def remove_request(req_id):
    cs.put_doc("jeux_requests", [r for r in get_requests() if r["id"] != req_id])


def all_list_keys():
    return [k for k, _ in config.month_keys()] + [config.VIEUX_KEY]


def final_games():
    sel = get_admin_selected()
    out = []
    for lk in all_list_keys():
        for g in load_games(lk):
            ckey = f"{lk}::{g['id']}"
            if ckey in sel:
                out.append((ckey, g))
    return out


def get_loans():
    return cs.get_doc("jeux_loans", {})


def toggle_loan(ckey, user_id, value):
    loans = get_loans()
    lst = set(loans.get(ckey, []))
    lst.add(user_id) if value else lst.discard(user_id)
    loans[ckey] = sorted(lst)
    cs.put_doc("jeux_loans", loans)


def set_loan(ckey, user_id, value):
    toggle_loan(ckey, user_id, value)
