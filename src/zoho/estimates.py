"""Gestion des estimates (soumissions) Zoho Invoice."""

import requests
from src.zoho.auth import get_headers
from src.config import ZOHO_ORG_ID

_BASE_URL = "https://www.zohoapis.com/invoice/v3"


def _next_estimate_number(customer_name: str) -> str:
    """Génère le prochain numéro d'estimate: NomClient-01, NomClient-02, etc."""
    # Nettoyer le nom client pour en faire un préfixe
    prefix = customer_name.strip().replace(" ", " ")

    resp = requests.get(
        f"{_BASE_URL}/estimates",
        headers=get_headers(),
        params={
            "organization_id": ZOHO_ORG_ID,
            "per_page": 200,
            "customer_name": customer_name,
        },
    )
    resp.raise_for_status()
    estimates = resp.json().get("estimates", [])

    # Compter les estimates de ce client
    max_num = 0
    client_count = 0
    for e in estimates:
        num = e.get("estimate_number", "")
        # Chercher le pattern "NomClient-XX"
        if num.lower().startswith(prefix.lower()):
            suffix = num[len(prefix):].strip().lstrip("-").strip()
            try:
                n = int(suffix)
                max_num = max(max_num, n)
            except ValueError:
                pass
        # Compter toutes les estimates du client (quel que soit le format du numéro)
        if e.get("customer_name", "").lower() == customer_name.lower():
            client_count += 1

    # Prendre le max entre le compteur séquentiel et le nombre total d'estimates
    next_num = max(max_num, client_count) + 1
    return f"{prefix}-{next_num:02d}"


def get_contacts(search: str = None) -> list[dict]:
    """Récupère les contacts Zoho (clients)."""
    params = {"organization_id": ZOHO_ORG_ID}
    if search:
        params["contact_name"] = search

    resp = requests.get(
        f"{_BASE_URL}/contacts",
        headers=get_headers(),
        params=params,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("contacts", [])


def create_estimate(
    customer_id: str,
    line_items: list[dict],
    estimate_number: str = None,
    reference_number: str = None,
    notes: str = None,
    customer_name: str = None,
) -> dict:
    """Crée une soumission (estimate) dans Zoho Invoice.

    Args:
        customer_id: ID du client Zoho
        line_items: Liste de dicts avec:
            - item_id: ID item Zoho (optionnel si name fourni)
            - name: Nom du produit
            - quantity: Quantité
            - rate: Prix unitaire
            - description: Description (optionnel)
        estimate_number: Numéro de soumission (optionnel, auto-généré)
        reference_number: Référence interne (optionnel)
        notes: Notes pour le client (optionnel)
    """
    if not estimate_number:
        # Récupérer le nom du client si pas fourni
        if not customer_name:
            contacts = get_contacts()
            for c in contacts:
                if c.get("contact_id") == customer_id:
                    customer_name = c.get("contact_name", "Soumission")
                    break
            else:
                customer_name = "Soumission"
        estimate_number = _next_estimate_number(customer_name)

    payload = {
        "customer_id": customer_id,
        "line_items": line_items,
        "estimate_number": estimate_number,
    }
    if reference_number:
        payload["reference_number"] = reference_number
    if notes:
        payload["notes"] = notes

    resp = requests.post(
        f"{_BASE_URL}/estimates",
        headers=get_headers(),
        params={"organization_id": ZOHO_ORG_ID},
        json=payload,
    )
    data = resp.json()

    if resp.status_code >= 400 or data.get("code") != 0:
        raise RuntimeError(f"Erreur création estimate: {data.get('message', resp.text)}")

    return data.get("estimate", {})


def push_finalized_quote(request_id: int, customer_id: str,
                         customer_name: str = None,
                         estimate_number: str = None,
                         notes: str = None) -> dict:
    """Pousse une soumission finalisée vers Zoho Invoice.

    Lit les données finalisées depuis la base locale et crée l'estimate.
    """
    from src.db.database import get_session
    from src.db.models import QuoteLine, QuoteSuggestion, Product
    from src.pricing.pricing_engine import calculate_selling_price

    session = get_session()
    try:
        lines = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id,
            QuoteLine.status == "finalized",
        ).all()

        if not lines:
            raise ValueError(f"Aucune ligne finalisée pour la demande #{request_id}")

        line_items = []
        for line in lines:
            # Trouver le produit sélectionné
            sugg = session.query(QuoteSuggestion).filter(
                QuoteSuggestion.quote_line_id == line.id,
                QuoteSuggestion.is_selected == True,
            ).first()

            # Si pas de sélection explicite, prendre la suggestion #1
            if not sugg:
                sugg = session.query(QuoteSuggestion).filter(
                    QuoteSuggestion.quote_line_id == line.id,
                    QuoteSuggestion.rank == 1,
                ).first()

            if not sugg:
                continue

            product = session.get(Product, sugg.product_id)
            if not product:
                continue

            # Calculer le prix de vente avec la stratégie de pricing
            sku = product.internal_sku or product.source_sku or ""
            pricing = calculate_selling_price(
                product_cost=product.price,
                client_price=line.client_price,
                product_sku=sku,
            )

            item_data = {
                "name": product.title,
                "quantity": line.quantity or 1,
                "rate": pricing["selling_price"],
            }

            # Si le produit a un source_sku Zoho (via sync ou import), l'utiliser
            if product.source_sku and product.source_sku.isdigit() and len(product.source_sku) > 10:
                item_data["item_id"] = product.source_sku

            # Construire la description avec économies si prix client disponible
            desc_parts = []

            # Équivalence produit client
            if line.raw_description != product.title:
                desc_parts.append(f"Équivalent au {line.raw_description}")

            # Économies (seulement si le client a fourni son prix)
            if line.client_price and line.client_price > 0:
                desc_parts.append(f"Vous payez actuellement : {line.client_price:.2f}$")
                if pricing["savings_pct"] and pricing["savings_pct"] > 0:
                    desc_parts.append(f"Économie de : {pricing['savings_pct']:.0f}%")

            if desc_parts:
                item_data["description"] = "\n".join(desc_parts)

            line_items.append(item_data)

        if not line_items:
            raise ValueError("Aucun produit à envoyer dans l'estimate")

        return create_estimate(
            customer_id=customer_id,
            line_items=line_items,
            estimate_number=estimate_number,
            customer_name=customer_name,
            notes=notes or "Soumission générée par Neobex Quotes",
        )

    finally:
        session.close()
