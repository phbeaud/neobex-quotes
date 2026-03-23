"""Page Upload — Nouvelle soumission."""

import tempfile
import streamlit as st
from pathlib import Path


def render():
    st.header("📤 Nouvelle soumission")
    st.markdown("Déposez le fichier du client pour lancer l'analyse de matching.")

    uploaded_file = st.file_uploader(
        "Fichier client",
        type=["xlsx", "xls", "csv", "pdf", "txt"],
        help="Excel, CSV, PDF ou fichier texte contenant la liste de produits du client",
    )

    if uploaded_file:
        st.info(f"Fichier : **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Analyser", type="primary", use_container_width=True):
                _run_analysis(uploaded_file)

        # Si une analyse vient d'être faite, afficher le résumé
        if st.session_state.current_request_id:
            _show_summary(st.session_state.current_request_id)


def _run_analysis(uploaded_file):
    """Lance l'analyse du fichier uploadé."""
    # Sauvegarder le fichier dans un dossier temporaire
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # Debug: vérifier l'engine avant analyse
    import src.db.database as _dbmod
    _eng = _dbmod._get_engine()
    st.warning(f"🔧 Engine URL: {_eng.url}")

    with st.spinner("Analyse en cours..."):
        try:
            from src.main import run_analysis
            request_id = run_analysis(tmp_path)
            st.session_state.current_request_id = request_id
            st.success(f"Analyse terminée — Demande #{request_id}")
        except Exception as e:
            st.error(f"Erreur lors de l'analyse : {e}")


def _show_summary(request_id: int):
    """Affiche le résumé des résultats de matching."""
    from src.dashboard.state import get_db_session
    from src.db.models import QuoteLine

    session = get_db_session()
    try:
        lines = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id
        ).all()

        total = len(lines)
        auto = sum(1 for l in lines if l.status == "auto_approved")
        review = sum(1 for l in lines if l.status == "to_review")
        low = sum(1 for l in lines if l.status == "low_match")
        not_found = sum(1 for l in lines if l.status == "not_found")

        st.markdown("### Résultats")
        cols = st.columns(5)
        cols[0].metric("Total", total)
        cols[1].metric("Auto-approuvés", auto, delta=None)
        cols[2].metric("À revoir", review)
        cols[3].metric("Match faible", low)
        cols[4].metric("Non trouvés", not_found)

        # Barre de progression
        if total > 0:
            pct_ok = (auto + review) / total * 100
            st.progress(pct_ok / 100, text=f"{pct_ok:.0f}% des produits matchés")

        st.markdown("---")
        if st.button("➡️ Passer à la validation", use_container_width=True):
            st.session_state.page = "validation"
            st.rerun()
    finally:
        session.close()
