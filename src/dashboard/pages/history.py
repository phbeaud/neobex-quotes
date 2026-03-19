"""Page Historique — Liste des soumissions passées."""

import streamlit as st
import pandas as pd


def render():
    st.header("📚 Historique des soumissions")

    from src.dashboard.state import get_db_session
    from src.db.models import QuoteRequest, QuoteLine

    session = get_db_session()
    try:
        requests = session.query(QuoteRequest).order_by(
            QuoteRequest.created_at.desc()
        ).all()

        if not requests:
            st.info("Aucune soumission enregistrée.")
            return

        rows = []
        for req in requests:
            lines = session.query(QuoteLine).filter(
                QuoteLine.quote_request_id == req.id
            ).all()

            total_lines = len(lines)
            finalized = sum(1 for l in lines if l.status == "finalized")
            auto = sum(1 for l in lines if l.status == "auto_approved")

            rows.append({
                "ID": req.id,
                "Fichier": req.source_file.split("/")[-1] if req.source_file else "—",
                "Type": req.source_type or "—",
                "Date": req.created_at.strftime("%Y-%m-%d %H:%M") if req.created_at else "—",
                "Statut": req.status,
                "Lignes": total_lines,
                "Finalisées": finalized,
                "Auto-approuvées": auto,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Permettre de charger une demande existante
        st.markdown("---")
        selected_id = st.selectbox(
            "Charger une demande existante",
            options=[r["ID"] for r in rows],
            format_func=lambda x: f"#{x} — {next(r['Fichier'] for r in rows if r['ID'] == x)}",
        )

        if st.button("📂 Charger cette demande"):
            st.session_state.current_request_id = selected_id
            st.session_state.page = "validation"
            st.rerun()

    finally:
        session.close()
