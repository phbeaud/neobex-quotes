"""Règles de priorisation produit.

Certains produits Neobex doivent toujours être proposés en premier
quand le client demande un type de produit spécifique.

Chaque règle contient:
- keywords: mots-clés qui déclenchent la règle (dans la description normalisée)
- preferred_skus: SKUs à prioriser (ordre = priorité)
- boost: points de score à ajouter au produit priorisé
"""
from __future__ import annotations

# ── Règles de priorisation ─────────────────────────────────
# Ajouter de nouvelles règles ici au besoin.
PRIORITY_RULES: list[dict] = [
    {
        "name": "Gants nitrile → AdvanCare",
        "keywords": ["gant nitrile", "nitrile glove"],
        "preferred_skus": ["ANBM10014"],  # AdvanCare 3,5 mil
        "boost": 15,
    },
    {
        "name": "Gants vinyle → Neobex vinyle synthétique",
        "keywords": ["gant vinyle", "vinyl glove"],
        "preferred_skus": ["VGPF3001"],
        "boost": 15,
    },
    {
        "name": "Papier hygiénique → Everest",
        "keywords": ["papier hygiénique", "papier hygienique", "bathroom tissue"],
        "preferred_skus": ["SNS-48420"],
        "boost": 10,
    },
    {
        "name": "Javel → Lavo Pro",
        "keywords": ["javel", "bleach", "eau de javel"],
        "preferred_skus": ["LAV-044015"],
        "boost": 10,
    },
    {
        "name": "Désinfectant mains → MED 2",
        "keywords": ["désinfectant main", "desinfectant main", "hand sanitizer", "purell"],
        "preferred_skus": ["INO-MED2-500"],
        "boost": 10,
    },
]


def apply_priority_boost(
    candidates: list[dict],
    normalized_desc: str,
    products_by_id: dict,
) -> list[dict]:
    """Applique les boosts de priorisation aux candidats.

    Args:
        candidates: liste de dicts {product_id, score, reason, ...}
        normalized_desc: description normalisée du produit client
        products_by_id: dict {product_id: Product} pour accès rapide aux SKUs

    Returns:
        Liste de candidats avec scores ajustés, re-triée.
    """
    desc_lower = normalized_desc.lower()

    for rule in PRIORITY_RULES:
        # Vérifier si la description matche les keywords de cette règle
        matched = any(kw in desc_lower for kw in rule["keywords"])
        if not matched:
            continue

        # Appliquer le boost aux produits préférés
        for cand in candidates:
            product = products_by_id.get(cand["product_id"])
            if not product:
                continue

            sku = (product.internal_sku or "").upper()
            source_sku = (product.source_sku or "").upper()

            if any(
                psku.upper() in (sku, source_sku)
                for psku in rule["preferred_skus"]
            ):
                cand["score"] = min(cand["score"] + rule["boost"], 100.0)
                cand["reason"] = f"{cand.get('reason', '')} +priorité:{rule['name']}"

    # Re-trier par score décroissant
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates
