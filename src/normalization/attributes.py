"""Attributs critiques par catégorie — règles métier bloquantes."""

# Attributs qui doivent concorder pour qu'un match soit valide
CRITICAL_ATTRIBUTES = {
    "epi": ["size", "material", "color"],
    "papier": ["format"],
    "chimique": ["usage"],
    "sacs": ["dimension"],
    "emballage": ["format"],
    "entretien": [],
    "autre": [],
}


def get_critical_attributes(category: str) -> list[str]:
    """Retourne les attributs critiques pour une catégorie donnée."""
    return CRITICAL_ATTRIBUTES.get(category, [])


def check_critical_match(category: str, source_attrs: dict, target_attrs: dict) -> bool:
    """Vérifie que les attributs critiques concordent.

    Retourne True si tous les attributs critiques présents dans les deux
    descriptions sont identiques, ou si l'un des deux n'a pas l'attribut.
    """
    critical = get_critical_attributes(category)

    for attr in critical:
        source_val = source_attrs.get(attr)
        target_val = target_attrs.get(attr)

        # Si les deux ont une valeur et qu'elles diffèrent -> bloquant
        if source_val and target_val and source_val != target_val:
            return False

    return True
