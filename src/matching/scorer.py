"""Calcul du score final de confiance."""


def compute_final_score(candidate: dict, category: str) -> dict:
    """Ajuste le score final en fonction de la raison du match.

    Les matchs exacts obtiennent un bonus, les fuzzy restent tels quels.
    """
    score = candidate["score"]
    reason = candidate["reason"]

    # Bonus par type de match
    bonuses = {
        "equivalence_connue": 0,   # déjà à 100
        "exact_sku": 0,            # déjà à 100
        "exact_description": 0,    # déjà à 98
        "synonym": 0,              # déjà à 95
        "fuzzy_match": 0,          # score rapidfuzz brut
    }

    score += bonuses.get(reason, 0)
    score = min(score, 100.0)

    return {**candidate, "score": round(score, 1)}
