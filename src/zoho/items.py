"""Gestion des items Zoho Invoice."""

import requests
from src.zoho.auth import get_headers
from src.config import ZOHO_ORG_ID

_BASE_URL = "https://www.zohoapis.com/invoice/v3"


def get_all_items() -> list[dict]:
    """Récupère tous les items actifs depuis Zoho Invoice."""
    items = []
    page = 1

    while True:
        resp = requests.get(
            f"{_BASE_URL}/items",
            headers=get_headers(),
            params={
                "organization_id": ZOHO_ORG_ID,
                "page": page,
                "per_page": 200,
                "filter_by": "Status.Active",
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"Erreur Zoho Items: {data.get('message')}")

        batch = data.get("items", [])
        if not batch:
            break

        items.extend(batch)

        # Vérifier s'il y a d'autres pages
        page_context = data.get("page_context", {})
        if not page_context.get("has_more_page", False):
            break
        page += 1

    return items


def sync_items() -> int:
    """Synchronise les items Zoho dans la base locale.

    Retourne le nombre de produits mis à jour/créés.
    """
    from src.db.database import get_session
    from src.db.models import Product
    from src.normalization.cleaner import normalize_line

    zoho_items = get_all_items()
    session = get_session()

    count = 0
    try:
        for item in zoho_items:
            item_id = str(item.get("item_id", ""))
            name = item.get("name", "")
            sku = item.get("sku", "")
            rate = item.get("rate", 0)
            unit = item.get("unit", "")
            description = item.get("description", "")
            status = item.get("status", "active")

            if status != "active" or not name:
                continue

            # Chercher un produit existant par source_sku (item_id Zoho)
            product = session.query(Product).filter(
                Product.source_sku == item_id,
                Product.source_name == "zoho",
            ).first()

            if not product:
                # Chercher par SKU interne
                if sku:
                    product = session.query(Product).filter(
                        Product.internal_sku == sku,
                    ).first()

            if product:
                # Mise à jour
                product.title = name
                product.price = rate
                product.uom = unit
                product.description = description
                product.normalized_description = normalize_line(name)
                product.is_active = True
            else:
                # Nouveau produit
                product = Product(
                    title=name,
                    internal_sku=sku or None,
                    source_name="zoho",
                    source_sku=item_id,
                    price=rate,
                    uom=unit,
                    description=description,
                    normalized_description=normalize_line(name),
                    is_active=True,
                    category="autre",  # Sera recatégorisé
                )
                session.add(product)

            count += 1

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return count


def create_item(name: str, rate: float, sku: str = None,
                unit: str = None, description: str = None) -> dict:
    """Crée un nouvel item dans Zoho Invoice."""
    payload = {
        "name": name,
        "rate": rate,
    }
    if sku:
        payload["sku"] = sku
    if unit:
        payload["unit"] = unit
    if description:
        payload["description"] = description

    resp = requests.post(
        f"{_BASE_URL}/items",
        headers=get_headers(),
        params={"organization_id": ZOHO_ORG_ID},
        json=payload,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"Erreur création item: {data.get('message')}")

    return data.get("item", {})
