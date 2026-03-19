"""Page Clients — Liste des clients Zoho."""

import streamlit as st
import pandas as pd


def render():
    st.header("👥 Clients Zoho")

    if st.button("🔄 Rafraîchir la liste"):
        st.cache_data.clear()
        st.rerun()

    contacts = _load_contacts()

    if not contacts:
        st.warning("Aucun contact trouvé dans Zoho.")
        return

    # Barre de recherche
    search = st.text_input("🔎 Rechercher", placeholder="Nom du client...")

    rows = []
    for c in contacts:
        name = c.get("contact_name", "")
        if search and search.lower() not in name.lower():
            continue
        rows.append({
            "Nom": name,
            "Entreprise": c.get("company_name", "—"),
            "Email": c.get("email", "—"),
            "Téléphone": c.get("phone", "—"),
            "Solde": f"{c.get('outstanding_receivable_amount', 0):.2f}$",
            "ID": c.get("contact_id", ""),
        })

    st.markdown(f"**{len(rows)}** clients trouvés")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Sélectionner un client pour le push
    if rows:
        st.markdown("---")
        selected = st.selectbox(
            "Sélectionner un client pour la prochaine soumission",
            options=range(len(rows)),
            format_func=lambda i: rows[i]["Nom"],
        )
        if st.button("✅ Utiliser ce client"):
            st.session_state.selected_customer_id = rows[selected]["ID"]
            st.session_state.selected_customer_name = rows[selected]["Nom"]
            st.success(f"Client sélectionné : {rows[selected]['Nom']}")


@st.cache_data(ttl=300)  # cache 5 min
def _load_contacts():
    """Charge les contacts depuis Zoho (avec cache)."""
    try:
        from src.zoho.estimates import get_contacts
        return get_contacts()
    except Exception as e:
        st.error(f"Erreur Zoho : {e}")
        return []
