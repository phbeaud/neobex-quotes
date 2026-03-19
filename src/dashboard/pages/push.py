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

        # Aperçu des lignes à envoyer
        st.markdown(f"### Aperçu — {len(finalized)} lignes à envoyer")

        preview_rows = []
        total = 0
        total_savings = 0
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
            qty = line.quantity or 1
            price = product.price if product else 0
            amount = qty * price
            total += amount

            savings_text = ""
            if line.client_price and price > 0:
                savings_pct = ((line.client_price - price) / line.client_price) * 100
                if savings_pct > 0:
                    savings_text = f"{savings_pct:.0f}%"
                    total_savings += (line.client_price - price) * qty

            preview_rows.append({
                "Description client": line.raw_description[:50],
                "Produit Neobex": product.title[:50] if product else "—",
                "Qté": qty,
                "Prix": f"{price:.2f}$",
                "Montant": f"{amount:.2f}$",
                "Prix client": f"{line.client_price:.2f}$" if line.client_price else "—",
                "Économie": savings_text,
            })

        st.dataframe(preview_rows, use_container_width=True, hide_index=True)

        # Totaux
        col1, col2, col3 = st.columns(3)
        col1.metric("Sous-total", f"{total:.2f}$")
        col2.metric("Économies client", f"{total_savings:.2f}$" if total_savings > 0 else "—")
        col3.metric("Lignes", len(finalized))

        st.markdown("---")

        # Sélection du client Zoho
        st.markdown("### Client Zoho")

        customer_search = st.text_input(
            "Rechercher un client",
            value=st.session_state.get("selected_customer_name", ""),
            placeholder="Tapez le nom du client...",
        )

        if customer_search and st.button("🔎 Chercher"):
            _search_contacts(customer_search)

        # Afficher le client sélectionné
        if st.session_state.get("selected_customer_id"):
            st.success(
                f"Client : **{st.session_state.selected_customer_name}** "
                f"(ID: {st.session_state.selected_customer_id})"
            )

            st.markdown("---")
            if st.button("📨 Créer la soumission dans Zoho", type="primary", use_container_width=True):
                _push_to_zoho(request_id)

    finally:
        session.close()


def _search_contacts(search: str):
    """Recherche des contacts dans Zoho."""
    try:
        from src.zoho.estimates import get_contacts
        contacts = get_contacts(search)

        if not contacts:
            st.warning(f"Aucun client trouvé pour '{search}'")
            return

        # Afficher les résultats
        options = {
            c["contact_name"]: c["contact_id"]
            for c in contacts[:10]
        }

        selected_name = st.selectbox(
            "Sélectionnez le client",
            options=list(options.keys()),
        )

        if selected_name:
            st.session_state.selected_customer_id = options[selected_name]
            st.session_state.selected_customer_name = selected_name
            st.rerun()

    except Exception as e:
        st.error(f"Erreur Zoho : {e}")


def _push_to_zoho(request_id: int):
    """Pousse la soumission vers Zoho."""
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
            st.success(
                f"✅ Soumission **{est_num}** créée avec succès!\n\n"
                f"- Total : {est_total}$\n"
                f"- Client : {customer_name}\n"
                f"- ID Zoho : {estimate.get('estimate_id', 'N/A')}"
            )
        except Exception as e:
            st.error(f"Erreur lors du push : {e}")
