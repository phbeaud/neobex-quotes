"""Règles métier pour le matching — filtrage des incompatibilités."""
from __future__ import annotations

from src.db.models import Product
from src.normalization.parser import extract_attributes
from src.normalization.attributes import check_critical_match


def apply_rules(
    candidates: list[dict],
    source_desc: str,
    source_category: str,
    products: list[Product],
) -> list[dict]:
    """Applique les règles métier pour éliminer les matchs invalides.

    Règle 1: Catégorie incompatible -> rejeté
    Règle 2: Attributs critiques qui ne concordent pas -> rejeté
    """
    if not candidates:
        return []

    source_attrs = extract_attributes(source_desc)
    product_map = {p.id: p for p in products}
    filtered = []

    for candidate in candidates:
        product = product_map.get(candidate["product_id"])
        if not product:
            continue

        # Règle 1: catégorie incompatible
        if source_category != "autre" and product.category != "autre":
            if product.category != source_category:
                continue

        # Règle 2: attributs critiques
        target_desc = product.normalized_description or product.title
        target_attrs = extract_attributes(target_desc)

        if not check_critical_match(source_category, source_attrs, target_attrs):
            continue

        filtered.append(candidate)

    return filtered
