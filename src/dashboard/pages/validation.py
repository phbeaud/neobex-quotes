"""Page Validation — Tableau interactif de matching."""

import streamlit as st
import pandas as pd
from datetime import datetime


def render():
    st.header("✅ Validation des matchs")

    request_id = st.session_state.get("current_request_id")
    if not request_id:
        st.warning("Aucune demande active. Uploadez un fichier d'abord.")
        if st.button("📤 Aller à l'upload"):
            st.session_state.page = "upload"
            st.rerun()
        return

    from src.dashboard.state import get_db_session
    from src.db.models import QuoteLine, QuoteSuggestion, Product

    session = get_db_session()
    try:
        lines = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id
        ).all()

        if not lines:
            st.warning(f"Aucune ligne pour la demande #{request_id}")
            return

        st.info(f"Demande #{request_id} — {len(lines)} produits")

        # Construire le DataFrame éditable
        rows = []
        for line in lines:
            suggestions = session.query(QuoteSuggestion).filter(
                QuoteSuggestion.quote_line_id == line.id
            ).order_by(QuoteSuggestion.rank).all()

            # Construire les options de suggestions
            options = {}
            for s in suggestions:
                product = session.get(Product, s.product_id)
                if product:
                    options[s.rank] = {
                        "label": f"{s.rank}. {product.title[:60]} ({s.score:.0f}%)",
                        "title": product.title,
                        "sku": product.internal_sku or "",
                        "price": product.price or 0,
                    }

            # Choix par défaut
            default_choice = ""
            if line.status == "auto_approved" and 1 in options:
                default_choice = options[1]["label"]

            row = {
                "line_id": line.id,
                "description_client": line.raw_description,
                "quantité": line.quantity or 1,
                "catégorie": line.detected_category or "",
                "statut": _status_emoji(line.status),
                "suggestion_1": options.get(1, {}).get("label", "—"),
                "suggestion_2": options.get(2, {}).get("label", "—"),
                "suggestion_3": options.get(3, {}).get("label", "—"),
                "choix": default_choice if default_choice else (
                    options.get(1, {}).get("label", "") if options else ""
                ),
                "prix_client": line.client_price or None,
                "commentaire": "",
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # Afficher le tableau éditable
        st.markdown("### Tableau de validation")
        st.caption("Modifiez le choix, le prix client et les commentaires, puis finalisez.")

        edited_df = st.data_editor(
            df,
            column_config={
                "line_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "description_client": st.column_config.TextColumn("Description client", disabled=True, width="large"),
                "quantité": st.column_config.NumberColumn("Qté", width="small"),
                "catégorie": st.column_config.TextColumn("Cat.", disabled=True, width="small"),
                "statut": st.column_config.TextColumn("Statut", disabled=True, width="small"),
                "suggestion_1": st.column_config.TextColumn("Suggestion 1", disabled=True, width="medium"),
                "suggestion_2": st.column_config.TextColumn("Suggestion 2", disabled=True, width="medium"),
                "suggestion_3": st.column_config.TextColumn("Suggestion 3", disabled=True, width="medium"),
                "choix": st.column_config.SelectboxColumn(
                    "Choix",
                    options=[r.get("suggestion_1", "") for r in rows]
                    + [r.get("suggestion_2", "") for r in rows]
                    + [r.get("suggestion_3", "") for r in rows],
                    width="medium",
                ),
                "prix_client": st.column_config.NumberColumn(
                    "Prix client $", format="%.2f", width="small"
                ),
                "commentaire": st.column_config.TextColumn("Commentaire", width="medium"),
            },
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
        )

        # Bouton finaliser
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Finaliser la soumission", type="primary", use_container_width=True):
                _finalize(session, edited_df, request_id)
        with col2:
            if st.button("🚀 Finaliser et passer au push Zoho", use_container_width=True):
                _finalize(session, edited_df, request_id)
                st.session_state.page = "push"
                st.rerun()

    finally:
        session.close()


def _finalize(session, edited_df: pd.DataFrame, request_id: int):
    """Finalise les lignes éditées : écrit en DB + crée les équivalences."""
    from src.db.models import (
        QuoteLine, QuoteSuggestion, Product, ValidationHistory, Equivalence,
    )

    count = 0
    equiv_count = 0

    for _, row in edited_df.iterrows():
        line_id = int(row["line_id"])
        choix = str(row.get("choix", "")).strip()
        client_price = row.get("prix_client")
        comment = str(row.get("commentaire", "")).strip()

        line = session.get(QuoteLine, line_id)
        if not line:
            continue

        # Mettre à jour le prix client
        if pd.notna(client_price):
            try:
                line.client_price = float(client_price)
            except (ValueError, TypeError):
                pass

        # Résoudre le produit choisi depuis le label "1. Titre (score%)"
        product = None
        if choix and choix != "—":
            # Extraire le rank du choix ("1. Titre... (85%)" → rank 1)
            rank = None
            if choix and choix[0].isdigit() and ". " in choix[:4]:
                try:
                    rank = int(choix[0])
                except ValueError:
                    pass

            if rank:
                sugg = session.query(QuoteSuggestion).filter(
                    QuoteSuggestion.quote_line_id == line_id,
                    QuoteSuggestion.rank == rank,
                ).first()
                if sugg:
                    product = session.get(Product, sugg.product_id)
                    sugg.is_selected = True

        if product:
            # Historique
            history = ValidationHistory(
                quote_line_id=line_id,
                selected_product_id=product.id,
                previous_status=line.status,
                new_status="finalized",
                comment=comment if comment and comment.lower() != "nan" else None,
            )
            session.add(history)
            line.status = "finalized"
            count += 1

            # Équivalence pour apprentissage
            existing = session.query(Equivalence).filter(
                Equivalence.source_description == line.raw_description,
                Equivalence.matched_product_id == product.id,
            ).first()
            if not existing:
                equiv = Equivalence(
                    source_type="client",
                    source_name="validation_streamlit",
                    source_description=line.raw_description,
                    matched_product_id=product.id,
                    confidence_score=100.0,
                    validated_by="humain",
                    validated_at=datetime.now(),
                )
                session.add(equiv)
                equiv_count += 1

    session.commit()
    st.success(f"✅ {count} lignes finalisées, {equiv_count} nouvelles équivalences apprises")


def _status_emoji(status: str) -> str:
    return {
        "auto_approved": "✅",
        "to_review": "🔍",
        "low_match": "⚠️",
        "not_found": "❌",
        "finalized": "🏁",
        "pending": "⏳",
    }.get(status, status)
