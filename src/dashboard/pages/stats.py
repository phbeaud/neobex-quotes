"""Page Statistiques — Métriques de matching."""

import streamlit as st
import pandas as pd


def render():
    st.header("📊 Statistiques")

    from src.dashboard.state import get_db_session
    from src.db.models import Product, QuoteLine, QuoteRequest, Equivalence, QuoteSuggestion
    from sqlalchemy import func

    session = get_db_session()
    try:
        # Métriques globales
        total_products = session.query(func.count(Product.id)).scalar()
        total_equivs = session.query(func.count(Equivalence.id)).scalar()
        total_requests = session.query(func.count(QuoteRequest.id)).scalar()
        total_lines = session.query(func.count(QuoteLine.id)).scalar()

        st.markdown("### Vue d'ensemble")
        cols = st.columns(4)
        cols[0].metric("Produits en base", total_products)
        cols[1].metric("Équivalences", total_equivs)
        cols[2].metric("Soumissions", total_requests)
        cols[3].metric("Lignes traitées", total_lines)

        st.markdown("---")

        # Statuts de matching
        st.markdown("### Taux de matching")
        status_counts = session.query(
            QuoteLine.status, func.count()
        ).group_by(QuoteLine.status).all()

        if status_counts:
            status_df = pd.DataFrame(status_counts, columns=["Statut", "Nombre"])
            status_map = {
                "auto_approved": "✅ Auto-approuvé",
                "to_review": "🔍 À revoir",
                "low_match": "⚠️ Match faible",
                "not_found": "❌ Non trouvé",
                "finalized": "🏁 Finalisé",
                "pending": "⏳ En attente",
            }
            status_df["Statut"] = status_df["Statut"].map(lambda x: status_map.get(x, x))
            st.bar_chart(status_df.set_index("Statut"))

        # Catégories de produits
        st.markdown("### Produits par catégorie")
        cat_counts = session.query(
            Product.category, func.count()
        ).group_by(Product.category).all()

        if cat_counts:
            cat_df = pd.DataFrame(cat_counts, columns=["Catégorie", "Nombre"])
            cat_df = cat_df.sort_values("Nombre", ascending=False)
            st.bar_chart(cat_df.set_index("Catégorie"))

        # Sources de produits
        st.markdown("### Produits par source")
        source_counts = session.query(
            Product.source_name, func.count()
        ).group_by(Product.source_name).all()

        if source_counts:
            source_df = pd.DataFrame(source_counts, columns=["Source", "Nombre"])
            st.dataframe(source_df, use_container_width=True, hide_index=True)

        # Scores moyens
        st.markdown("### Qualité des matchs")
        avg_score = session.query(func.avg(QuoteSuggestion.score)).filter(
            QuoteSuggestion.rank == 1
        ).scalar()

        if avg_score:
            st.metric("Score moyen (suggestion #1)", f"{avg_score:.1f}%")

    finally:
        session.close()
