"""Moteur de matching principal — orchestre les étapes de recherche."""
from __future__ import annotations

from sqlalchemy.orm import Session as DbSession
from src.db.models import Product
from src.db import repository as repo
from src.matching.exact_match import try_exact_match
from src.matching.fuzzy_match import try_fuzzy_match
from src.matching.rules import apply_rules
from src.matching.scorer import compute_final_score
from src.matching.priority import apply_priority_boost
from src.config import MAX_SUGGESTIONS, FUZZY_THRESHOLD


def find_matches(
    session: DbSession,
    normalized_desc: str,
    category: str,
    products: list[Product],
) -> list[dict]:
    """Cherche les meilleurs produits correspondants pour une description.

    Ordre de recherche:
    1. Équivalence connue en DB
    2. Match exact SKU ou description
    3. Match fuzzy
    4. Application des règles métier (filtrage)
    5. Score final

    Retourne une liste triée de dicts: {product_id, score, reason}
    """
    # 1. Équivalence déjà validée (cherche sur description brute ET normalisée)
    equiv = repo.get_known_equivalence(session, normalized_desc)
    if equiv:
        return [{
            "product_id": equiv.matched_product_id,
            "score": 100.0,
            "reason": "equivalence_connue",
        }]

    # 1b. Aussi chercher avec la description non-normalisée (les équivalences
    # sont souvent stockées avec la description brute du client)
    from src.db.models import Equivalence
    from rapidfuzz import fuzz
    all_equivs = session.query(Equivalence).filter(
        Equivalence.validated_at.isnot(None),
    ).all()
    for eq in all_equivs:
        # Comparer la description normalisée contre la source_description normalisée
        from src.normalization.cleaner import normalize_line
        eq_norm = normalize_line(eq.source_description)
        score = fuzz.token_sort_ratio(normalized_desc, eq_norm)
        if score >= 95:
            return [{
                "product_id": eq.matched_product_id,
                "score": 100.0,
                "reason": "equivalence_connue",
            }]

    candidates = []

    # 2. Match exact
    exact = try_exact_match(normalized_desc, products)
    candidates.extend(exact)

    # 3. Match fuzzy (seulement si pas assez de résultats exacts)
    if len(candidates) < MAX_SUGGESTIONS:
        fuzzy = try_fuzzy_match(normalized_desc, products, threshold=FUZZY_THRESHOLD)
        # Éviter les doublons
        existing_ids = {c["product_id"] for c in candidates}
        for f in fuzzy:
            if f["product_id"] not in existing_ids:
                candidates.append(f)

    # 4. Appliquer les règles métier (filtre les incompatibilités)
    candidates = apply_rules(candidates, normalized_desc, category, products)

    # 5. Score final et tri
    candidates = [compute_final_score(c, category) for c in candidates]
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 6. Priorisation produit (boost certains produits préférés)
    products_by_id = {p.id: p for p in products}
    candidates = apply_priority_boost(candidates, normalized_desc, products_by_id)

    return candidates[:MAX_SUGGESTIONS]
