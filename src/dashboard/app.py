"""Neobex Quotes — Dashboard Streamlit."""

import sys
from pathlib import Path

# Ajouter la racine du projet au path (nécessaire pour Streamlit Cloud)
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import streamlit as st

st.set_page_config(
    page_title="Neobex Quotes",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.dashboard.state import init_state

init_state()

# --- Sidebar navigation ---
st.sidebar.title("Neobex Quotes")
st.sidebar.markdown("---")

pages = {
    "upload": "📤 Nouvelle soumission",
    "validation": "✅ Validation",
    "push": "🚀 Push Zoho",
    "history": "📚 Historique",
    "clients": "👥 Clients",
    "stats": "📊 Statistiques",
}

for key, label in pages.items():
    if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
        st.session_state.page = key

# Indicateur de demande active
if st.session_state.current_request_id:
    st.sidebar.markdown("---")
    st.sidebar.success(f"Demande active : #{st.session_state.current_request_id}")

st.sidebar.markdown("---")
st.sidebar.caption("Neobex Group — v2.0")

# --- Page routing ---
page = st.session_state.page

if page == "upload":
    from src.dashboard.pages.upload import render
    render()
elif page == "validation":
    from src.dashboard.pages.validation import render
    render()
elif page == "push":
    from src.dashboard.pages.push import render
    render()
elif page == "history":
    from src.dashboard.pages.history import render
    render()
elif page == "clients":
    from src.dashboard.pages.clients import render
    render()
elif page == "stats":
    from src.dashboard.pages.stats import render
    render()
