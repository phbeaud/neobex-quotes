"""Matching fuzzy via rapidfuzz — score combiné multi-scorer."""
from __future__ import annotations

from rapidfuzz import fuzz, process
from src.db.models import Product


def try_fuzzy_match(
    normalized_desc: str,
    products: list[Product],
    threshold: int = 65,
    limit: int = 10,
) -> list[dict]:
    """Cherche des correspondances fuzzy sur les descriptions normalisées.

    Score combiné = moyenne pondérée de 3 scorers:
    - token_sort_ratio (40%): gère les inversions de mots
    - token_set_ratio (35%): gère les sous-ensembles
    - ratio (25%): similarité directe, pénalise les descriptions très différentes

    Cela évite que token_set_ratio donne 100% pour des matchs partiels.
    """
    if not products:
        return []

    choices = {}
    for p in products:
        desc = p.normalized_description or p.title
        if desc:
            choices[p.id] = desc.lower()

    if not choices:
        return []

    query = normalized_desc.lower()

    # Calculer les scores pour chaque produit
    scores_by_product: dict[int, dict] = {}

    # Pass 1: token_sort_ratio pour le pré-filtre (rapide)
    pre_matches = process.extract(
        query, choices,
        scorer=fuzz.token_sort_ratio,
        limit=limit * 3,
        score_cutoff=max(threshold - 15, 40),
    )

    # Candidats = union des meilleurs de chaque scorer
    candidate_ids = {pid for _, _, pid in pre_matches}

    # Ajouter aussi les top résultats de token_set_ratio
    set_matches = process.extract(
        query, choices,
        scorer=fuzz.token_set_ratio,
        limit=limit * 2,
        score_cutoff=threshold,
    )
    for _, _, pid in set_matches:
        candidate_ids.add(pid)

    # Calculer le score combiné pour chaque candidat
    for pid in candidate_ids:
        desc = choices[pid]
        sort_score = fuzz.token_sort_ratio(query, desc)
        set_score = fuzz.token_set_ratio(query, desc)
        ratio_score = fuzz.ratio(query, desc)

        # Score combiné pondéré
        combined = (sort_score * 0.40) + (set_score * 0.35) + (ratio_score * 0.25)

        if combined >= threshold:
            # Déterminer la raison principale
            best_scorer = max(
                [("fuzzy_sort", sort_score), ("fuzzy_set", set_score), ("fuzzy_ratio", ratio_score)],
                key=lambda x: x[1],
            )
            scores_by_product[pid] = {
                "product_id": pid,
                "score": round(combined, 1),
                "reason": best_scorer[0],
            }

    results = sorted(scores_by_product.values(), key=lambda x: x["score"], reverse=True)
    return results[:limit]
