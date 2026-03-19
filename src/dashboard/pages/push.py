"""Page Push — Envoi vers Zoho Invoice."""

import streamlit as st


def render():
    st.header("🚀 Push vers Zoho Invoice")

    request_id = st.session_state.get("current_request_id")
    if not request_id:
        st.warning("Aucune demande active. Uploadez et validez un fichier d'abord.")
        return

    from src.dashboard.state import get_db_session
    from src.db.models import QuoteLine, QuoteSuggestion, Product
    from src.pricing.pricing_engine import calculate_selling_price
    from src.pricing.unit_converter import calculate_unit_conversion

    session = get_db_session()
    try:
        # Vérifier qu'il y a des lignes finalisées
        finalized = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id,
            QuoteLine.status == "finalized",
        ).all()

        if not finalized:
            st.warning("Aucune ligne finalisée. Retournez à la validation.")
            if st.button("⬅️ Retour validation"):
                st.session_state.page = "validation"
                st.rerun()
            return

        # Aperçu des lignes avec pricing réel
        st.markdown(f"### Aperçu — {len(finalized)} lignes à envoyer")

        preview_rows = []
        total_neobex = 0
        total_client = 0
        skipped_count = 0
        has_client_prices = False

        for line in finalized:
            sugg = session.query(QuoteSuggestion).filter(
                QuoteSuggestion.quote_line_id == line.id,
                QuoteSuggestion.is_selected == True,
            ).first()
            if not sugg:
                sugg = session.query(QuoteSuggestion).filter(
                    QuoteSuggestion.quote_line_id == line.id,
                    QuoteSuggestion.rank == 1,
                ).first()

            product = session.get(Product, sugg.product_id) if sugg else None
            if not product:
                continue

            qty = line.quantity or 1
            sku = product.internal_sku or product.source_sku or ""

            # Conversion d'unités
            unit_conv = calculate_unit_conversion(
                client_desc=line.raw_description,
                neobex_desc=product.title or product.description or "",
                neobex_uom=product.uom or "",
                client_price=line.client_price,
                neobex_price=product.price,
            )

            effective_client_price = line.client_price
            if unit_conv["has_conversion"] and unit_conv["adjusted_client_price"]:
                effective_client_price = unit_conv["adjusted_client_price"]

            # Calcul du prix de vente réel (stratégie pricing)
            pricing = calculate_selling_price(
                product_cost=product.price,
                client_price=effective_client_price,
                product_sku=sku,
            )

            selling_price = pricing["selling_price"]
            margin_pct = pricing["margin_pct"]
            strategy = pricing["strategy"]
            amount = qty * selling_price

            # Filtre marge < 5% (sauf prix fixes)
            if margin_pct < 5 and "prix_fixe" not in strategy:
                skipped_count += 1
                continue

            total_neobex += amount

            savings_text = ""
            client_price_text = "—"
            conversion_note = ""
            if line.client_price and line.client_price > 0:
                has_client_prices = True
                if unit_conv["has_conversion"]:
                    client_price_text = f"{line.client_price:.2f}$ → {effective_client_price:.2f}$"
                    conversion_note = f"×{unit_conv['conversion_factor']:.1f}"
                else:
                    client_price_text = f"{line.client_price:.2f}$"
                total_client += effective_client_price * qty
                if pricing["savings_pct"] and pricing["savings_pct"] > 0:
                    savings_text = f"{pricing['savings_pct']:.0f}%"

            preview_rows.append({
                "Description client": line.raw_description[:45],
                "Produit Neobex": product.title[:45] if product else "—",
                "Qté": int(qty),
                "Prix vente": f"{selling_price:.2f}$",
                "Montant": f"{amount:.2f}$",
                "Stratégie": strategy.split("(")[0].strip(),
                "Marge": f"{margin_pct:.0f}%",
                "Prix client": client_price_text,
                "Conv.": conversion_note,
                "Économie": savings_text,
            })

        st.dataframe(preview_rows, use_container_width=True, hide_index=True)

        # Totaux et métriques
        if skipped_count > 0:
            st.warning(f"⚠️ {skipped_count} produit(s) exclus (marge < 5%)")

        if has_client_prices and total_client > 0:
            savings_total = total_client - total_neobex
            savings_pct = (savings_total / total_client) * 100

            st.markdown("---")
            st.markdown("### 💰 Résumé des économies")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total client actuel", f"{total_client:.2f}$")
            col2.metric("Notre soumission", f"{total_neobex:.2f}$")
            col3.metric("Économie totale", f"{savings_total:.2f}$")
            col4.metric("% d'économie", f"{savings_pct:.1f}%")
        else:
            col1, col2 = st.columns(2)
            col1.metric("Total soumission", f"{total_neobex:.2f}$")
            col2.metric("Lignes", len(preview_rows))

        st.markdown("---")

        # ── Sélection / création du client Zoho ──
        st.markdown("### 👤 Client Zoho")

        col_search, col_create = st.columns([3, 1])
        with col_search:
            customer_input = st.text_input(
                "Nom du client",
                value=st.session_state.get("selected_customer_name", ""),
                placeholder="Tapez le nom du client...",
            )
        with col_create:
            st.markdown("<br>", unsafe_allow_html=True)
            auto_create = st.checkbox("Créer si inexistant", value=True)

        if customer_input and st.button("🔎 Chercher / Créer le client"):
            _find_or_create_contact(customer_input, auto_create)

        # Afficher le client sélectionné
        if st.session_state.get("selected_customer_id"):
            created_label = " (nouveau)" if st.session_state.get("customer_created") else ""
            st.success(
                f"Client : **{st.session_state.selected_customer_name}**{created_label} "
                f"(ID: {st.session_state.selected_customer_id})"
            )

            st.markdown("---")
            if st.button("📨 Créer la soumission dans Zoho", type="primary", use_container_width=True):
                _push_to_zoho(request_id)

    finally:
        session.close()


def _find_or_create_contact(name: str, auto_create: bool = True):
    """Recherche intelligente + création auto du client Zoho."""
    try:
        from src.zoho.contacts import find_or_create_contact, search_contacts

        with st.spinner(f"Recherche de '{name}' dans Zoho..."):
            result = find_or_create_contact(name, auto_create=auto_create)

        if result["contact_id"]:
            st.session_state.selected_customer_id = result["contact_id"]
            st.session_state.selected_customer_name = result["contact_name"]
            st.session_state.customer_created = result.get("created", False)
            st.rerun()
        else:
            # Pas de match assez bon, montrer les suggestions
            st.warning(f"Aucun match exact pour '{name}'")
            suggestions = result.get("suggestions", [])
            if suggestions:
                st.markdown("**Suggestions :**")
                for s in suggestions:
                    col1, col2 = st.columns([4, 1])
                    col1.write(f"{s['contact_name']} ({s['score']:.0f}%)")
                    if col2.button("Utiliser", key=f"use_{s['contact_id']}"):
                        st.session_state.selected_customer_id = s["contact_id"]
                        st.session_state.selected_customer_name = s["contact_name"]
                        st.session_state.customer_created = False
                        st.rerun()

    except Exception as e:
        st.error(f"Erreur Zoho : {e}")


def _push_to_zoho(request_id: int):
    """Pousse la soumission vers Zoho avec résumé d'économies."""
    customer_id = st.session_state.selected_customer_id
    customer_name = st.session_state.selected_customer_name

    with st.spinner("Envoi vers Zoho Invoice..."):
        try:
            from src.zoho.estimates import push_finalized_quote
            estimate = push_finalized_quote(
                request_id=request_id,
                customer_id=customer_id,
                customer_name=customer_name,
            )
            est_num = estimate.get("estimate_number", "N/A")
            est_total = estimate.get("total", 0)

            st.balloons()

            # Résumé principal
            st.success(
                f"✅ Soumission **{est_num}** créée avec succès!\n\n"
                f"- Total : {est_total}$\n"
                f"- Client : {customer_name}\n"
                f"- ID Zoho : {estimate.get('estimate_id', 'N/A')}"
            )

            # Résumé pricing
            summary = estimate.get("_pricing_summary", {})
            if summary:
                if summary.get("items_skipped", 0) > 0:
                    st.warning(
                        f"⚠️ {summary['items_skipped']} produit(s) exclus (marge < 5%)"
                    )

                if "economie_pct" in summary:
                    st.info(
                        f"💰 **Économie totale pour le client : "
                        f"{summary['economie_totale']:.2f}$ ({summary['economie_pct']:.1f}%)**\n\n"
                        f"Le client payait {summary['total_client_actuel']:.2f}$ "
                        f"→ Notre soumission : {summary['total_neobex']:.2f}$"
                    )

        except Exception as e:
            st.error(f"Erreur lors du push : {e}")
