"""Matching exact — SKU, description normalisée, synonymes."""
from __future__ import annotations

from src.db.models import Product


def try_exact_match(normalized_desc: str, products: list[Product]) -> list[dict]:
    """Cherche des correspondances exactes.

    1. SKU exact
    2. Description normalisée identique
    3. Présence dans les synonymes du produit
    """
    results = []

    for p in products:
        # Match exact sur SKU
        if p.internal_sku and p.internal_sku.lower() == normalized_desc.lower():
            results.append({
                "product_id": p.id,
                "score": 100.0,
                "reason": "exact_sku",
            })
            continue

        # Match exact sur description normalisée
        if p.normalized_description and p.normalized_description.lower() == normalized_desc.lower():
            results.append({
                "product_id": p.id,
                "score": 98.0,
                "reason": "exact_description",
            })
            continue

        # Match sur synonymes
        if p.synonyms:
            syns = [s.strip().lower() for s in p.synonyms.split(",")]
            if normalized_desc.lower() in syns:
                results.append({
                    "product_id": p.id,
                    "score": 95.0,
                    "reason": "synonym",
                })
                continue

    return results
