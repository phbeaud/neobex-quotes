"""Page Validation — Interface intelligente avec alertes prix."""

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
    from src.pricing.pricing_engine import calculate_selling_price
    from src.pricing.unit_converter import compare_units, extract_unit_info

    session = get_db_session()
    try:
        lines = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id
        ).order_by(QuoteLine.id).all()

        if not lines:
            st.warning(f"Aucune ligne pour la demande #{request_id}")
            return

        # Initialize session state for decisions
        if "line_decisions" not in st.session_state:
            st.session_state.line_decisions = {}

        st.info(f"Demande #{request_id} — {len(lines)} produits")

        # Stats tracking
        total_client_spend = 0
        total_neobex_spend = 0
        kept_count = 0
        removed_count = 0
        no_match_count = 0

        for line in lines:
            suggestions = session.query(QuoteSuggestion).filter(
                QuoteSuggestion.quote_line_id == line.id
            ).order_by(QuoteSuggestion.rank).all()

            # Get best suggestion product
            best_product = None
            best_score = 0
            all_suggestions = []
            for s in suggestions:
                product = session.get(Product, s.product_id)
                if product:
                    all_suggestions.append({
                        "rank": s.rank,
                        "product": product,
                        "score": s.score,
                        "reason": s.reason,
                    })
                    if s.rank == 1:
                        best_product = product
                        best_score = s.score

            # Calculate pricing if we have a match
            pricing = None
            unit_comparison = None
            if best_product and best_product.price:
                pricing = calculate_selling_price(
                    product_cost=best_product.price,
                    client_price=line.client_price,
                    product_sku=best_product.internal_sku,
                )
                # Unit conversion
                if line.client_price:
                    unit_comparison = compare_units(
                        client_desc=line.raw_description,
                        client_price=line.client_price,
                        client_uom=line.uom or "",
                        neobex_desc=best_product.title or best_product.description or "",
                        neobex_price=pricing["selling_price"],
                        neobex_uom=best_product.uom,
                        neobex_case_qty=best_product.case_qty,
                    )

            # Determine card status
            card_status = _get_card_status(line, pricing, best_product)

            # Get current decision
            decision_key = f"decision_{line.id}"
            current_decision = st.session_state.line_decisions.get(
                line.id, "keep" if card_status != "no_match" else "remove"
            )

            # Render the card
            _render_product_card(
                line=line,
                best_product=best_product,
                best_score=best_score,
                all_suggestions=all_suggestions,
                pricing=pricing,
                unit_comparison=unit_comparison,
                card_status=card_status,
                session=session,
            )

            # Track stats
            if current_decision == "keep" and pricing:
                qty = line.quantity or 1
                if line.client_price:
                    total_client_spend += line.client_price * qty
                total_neobex_spend += pricing["selling_price"] * qty
                kept_count += 1
            elif card_status == "no_match":
                no_match_count += 1
            else:
                removed_count += 1

        # Popular products to add
        st.markdown("---")
        _render_popular_products(session)

        # Summary section
        st.markdown("---")
        _render_summary(total_client_spend, total_neobex_spend, kept_count, removed_count, no_match_count)

        # Action buttons
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Finaliser la soumission", type="primary", use_container_width=True):
                _finalize(session, lines, request_id)
        with col2:
            if st.button("🚀 Finaliser et push Zoho", use_container_width=True):
                _finalize(session, lines, request_id)
                st.session_state.page = "push"
                st.rerun()

    finally:
        session.close()


def _get_card_status(line, pricing, best_product):
    """Determine the status of a product card."""
    if not best_product:
        return "no_match"
    if not pricing:
        return "no_price"

    savings_pct = pricing.get("savings_pct")
    margin_pct = pricing.get("margin_pct", 0)

    if savings_pct is None:
        # No client price - standard margin
        return "standard"

    if savings_pct > 0 and margin_pct >= 5:
        return "savings"  # Green - client saves money
    elif margin_pct < 5:
        return "no_margin"  # Red - we can't make enough margin
    else:
        return "more_expensive"  # Orange - we're more expensive


def _render_product_card(line, best_product, best_score, all_suggestions,
                          pricing, unit_comparison, card_status, session):
    """Render a single product validation card."""
    from src.db.models import Product

    # Status colors and emojis
    status_config = {
        "savings": ("🟢", "background-color: #d4edda"),
        "standard": ("🔵", "background-color: #d1ecf1"),
        "more_expensive": ("🟠", "background-color: #fff3cd"),
        "no_margin": ("🔴", "background-color: #f8d7da"),
        "no_match": ("⬛", "background-color: #e2e3e5"),
        "no_price": ("🔵", "background-color: #d1ecf1"),
    }
    emoji, _ = status_config.get(card_status, ("❓", ""))

    # Build title
    title = f"{emoji} {line.raw_description[:70]}"
    if pricing and pricing.get("savings_pct") is not None:
        savings = pricing["savings_pct"]
        if savings > 0:
            title += f"  — 💰 Économie {savings:.0f}%"
        else:
            title += f"  — ⚠️ +{abs(savings):.0f}% plus cher"

    with st.expander(title, expanded=(card_status in ("no_margin", "more_expensive", "no_match"))):
        if card_status == "no_match":
            st.error("**Aucun match trouvé** — Produit non disponible dans le catalogue")

            # Manual search
            search_key = f"search_{line.id}"
            search_term = st.text_input(
                "🔍 Recherche manuelle", key=search_key,
                placeholder="Tapez un mot-clé pour chercher dans le catalogue..."
            )
            if search_term:
                results = session.query(Product).filter(
                    Product.title.ilike(f"%{search_term}%"),
                    Product.is_active == True,
                ).limit(5).all()
                if results:
                    for p in results:
                        st.write(f"  • **{p.title[:60]}** — SKU: {p.internal_sku} — {p.price:.2f}$" if p.price else f"  • **{p.title[:60]}** — SKU: {p.internal_sku}")
                else:
                    st.caption("Aucun résultat")

            # Decision
            decision = st.radio(
                "Action", ["❌ Retirer de la soumission", "🔍 Chercher manuellement"],
                key=f"action_{line.id}", horizontal=True,
            )
            st.session_state.line_decisions[line.id] = "remove" if "Retirer" in decision else "search"
            return

        # Product match info
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**Match:** {best_product.title[:80]}")
            st.caption(f"SKU: {best_product.internal_sku} | Score: {best_score:.0f}% | Cat: {line.detected_category}")

        with col2:
            if pricing:
                st.metric(
                    "Notre prix",
                    f"{pricing['selling_price']:.2f}$",
                    delta=f"{pricing['savings_pct']:.0f}% économie" if pricing.get('savings_pct') and pricing['savings_pct'] > 0 else None,
                    delta_color="normal" if pricing.get('savings_pct', 0) > 0 else "inverse",
                )

        # Price details
        if pricing:
            cols = st.columns(4)
            with cols[0]:
                st.caption("Coût Neobex")
                st.write(f"**{best_product.price:.2f}$**" if best_product.price else "N/A")
            with cols[1]:
                st.caption("Prix client actuel")
                st.write(f"**{line.client_price:.2f}$**" if line.client_price else "N/A")
            with cols[2]:
                st.caption("Notre prix de vente")
                st.write(f"**{pricing['selling_price']:.2f}$**")
            with cols[3]:
                st.caption("Marge")
                st.write(f"**{pricing['margin_pct']:.1f}%**")

            st.caption(f"Stratégie: {pricing['strategy']}")

        # Unit conversion note
        if unit_comparison and unit_comparison.get("conversion_note"):
            st.info(f"📐 **Conversion unités:** {unit_comparison['conversion_note']}")

        # Handle problematic cases
        if card_status in ("no_margin", "more_expensive"):
            st.warning("⚠️ Notre prix est supérieur au prix client ou la marge est insuffisante.")

            # Show alternatives from same category
            alternatives = session.query(Product).filter(
                Product.category == line.detected_category,
                Product.is_active == True,
                Product.price.isnot(None),
                Product.id != best_product.id,
            ).order_by(Product.price.asc()).limit(5).all()

            if alternatives:
                st.markdown("**Alternatives moins chères :**")
                alt_options = ["Garder le produit actuel"]
                for i, alt in enumerate(alternatives):
                    if alt.price and line.client_price:
                        alt_pricing = calculate_selling_price(alt.price, line.client_price, alt.internal_sku)
                        if alt_pricing["savings_pct"] and alt_pricing["savings_pct"] > 0:
                            alt_options.append(
                                f"📦 {alt.title[:50]} — {alt_pricing['selling_price']:.2f}$ "
                                f"(💰 {alt_pricing['savings_pct']:.0f}% économie)"
                            )
                    elif alt.price:
                        alt_selling = round(alt.price * 1.33, 2)
                        alt_options.append(
                            f"📦 {alt.title[:50]} — {alt_selling:.2f}$"
                        )

                alt_options.append("❌ Retirer de la soumission")

                from src.pricing.pricing_engine import calculate_selling_price
                choice = st.radio(
                    "Choix", alt_options, key=f"alt_{line.id}",
                )

                if "Retirer" in choice:
                    st.session_state.line_decisions[line.id] = "remove"
                elif "Garder" in choice:
                    st.session_state.line_decisions[line.id] = "keep"
                else:
                    st.session_state.line_decisions[line.id] = "alternative"
            else:
                decision = st.radio(
                    "Action",
                    ["Garder quand même", "❌ Retirer de la soumission"],
                    key=f"action_{line.id}", horizontal=True,
                )
                st.session_state.line_decisions[line.id] = "remove" if "Retirer" in decision else "keep"
        else:
            # Good match - auto keep
            st.session_state.line_decisions[line.id] = "keep"

        # Show other suggestions if available
        if len(all_suggestions) > 1:
            with st.popover("Voir les autres suggestions"):
                for s in all_suggestions[1:]:
                    p = s["product"]
                    st.write(f"**{s['rank']}.** {p.title[:60]} — Score: {s['score']:.0f}%")
                    if p.price:
                        st.caption(f"   Coût: {p.price:.2f}$ | SKU: {p.internal_sku}")


def _render_summary(total_client, total_neobex, kept, removed, no_match):
    """Render the summary section at the bottom."""
    st.markdown("### 📊 Résumé de la soumission")

    cols = st.columns(4)
    with cols[0]:
        st.metric("Produits gardés", kept)
    with cols[1]:
        st.metric("Produits retirés", removed)
    with cols[2]:
        st.metric("Non trouvés", no_match)
    with cols[3]:
        if total_client > 0:
            total_savings_pct = ((total_client - total_neobex) / total_client) * 100
            st.metric(
                "Économie totale",
                f"{total_savings_pct:.1f}%",
                delta=f"{total_client - total_neobex:.2f}$",
            )
        else:
            st.metric("Total Neobex", f"{total_neobex:.2f}$")

    if total_client > 0:
        st.success(
            f"💰 Le client économise **{total_client - total_neobex:.2f}$** "
            f"soit **{((total_client - total_neobex) / total_client) * 100:.1f}%** "
            f"en passant chez Neobex!"
        )


def _finalize(session, lines, request_id):
    """Finalize the submission based on decisions."""
    from src.db.models import (
        QuoteLine, QuoteSuggestion, Product, ValidationHistory, Equivalence,
    )

    count = 0
    equiv_count = 0
    removed = 0

    for line in lines:
        decision = st.session_state.line_decisions.get(line.id, "keep")

        if decision == "remove":
            line.status = "removed"
            removed += 1
            continue

        # Find the selected suggestion (rank 1 by default)
        sugg = session.query(QuoteSuggestion).filter(
            QuoteSuggestion.quote_line_id == line.id,
            QuoteSuggestion.rank == 1,
        ).first()

        if not sugg:
            continue

        product = session.get(Product, sugg.product_id)
        if not product:
            continue

        sugg.is_selected = True

        # History
        history = ValidationHistory(
            quote_line_id=line.id,
            selected_product_id=product.id,
            previous_status=line.status,
            new_status="finalized",
        )
        session.add(history)
        line.status = "finalized"
        count += 1

        # Equivalence learning
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
    st.success(
        f"✅ {count} produits finalisés | {removed} retirés | "
        f"{equiv_count} nouvelles équivalences apprises"
    )


def _render_popular_products(session):
    """Section pour ajouter des produits populaires à la soumission."""
    from src.pricing.popular_products import POPULAR_PRODUCTS
    from src.db.models import Product

    st.markdown("### 📦 Ajouter des produits populaires")
    st.caption("Cochez les produits à ajouter à cette soumission (souvent demandés par les clients).")

    if "popular_selections" not in st.session_state:
        st.session_state.popular_selections = {}

    for category, products in POPULAR_PRODUCTS.items():
        with st.expander(category):
            for item in products:
                sku = item["sku"]
                label = item["label"]
                default = item.get("default", False)

                # Chercher le prix en base
                db_product = session.query(Product).filter(
                    Product.internal_sku == sku
                ).first()
                price_str = f" — {db_product.price:.2f}$" if db_product and db_product.price else ""

                checked = st.checkbox(
                    f"{label}{price_str}",
                    value=st.session_state.popular_selections.get(sku, False),
                    key=f"pop_{sku}",
                )
                st.session_state.popular_selections[sku] = checked

    # Compter les sélections
    selected = [sku for sku, v in st.session_state.popular_selections.items() if v]
    if selected:
        st.success(f"✅ {len(selected)} produit(s) populaire(s) sélectionné(s)")


def _status_emoji(status: str) -> str:
    return {
        "auto_approved": "✅",
        "to_review": "🔍",
        "low_match": "⚠️",
        "not_found": "❌",
        "finalized": "🏁",
        "removed": "🗑️",
        "pending": "⏳",
    }.get(status, status)
