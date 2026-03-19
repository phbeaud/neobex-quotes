"""Gestion du state Streamlit et session DB."""

import streamlit as st
from src.db.database import engine, Session


@st.cache_resource
def get_db_engine():
    """Retourne l'engine DB (singleton pour Streamlit)."""
    from src.db.database import init_db
    init_db()
    return engine


def get_db_session():
    """Retourne une session DB pour le request courant."""
    get_db_engine()  # s'assurer que la DB est initialisée
    return Session()


def init_state():
    """Initialise les clés de session state par défaut."""
    defaults = {
        "current_request_id": None,
        "selected_customer_id": None,
        "selected_customer_name": None,
        "page": "upload",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
