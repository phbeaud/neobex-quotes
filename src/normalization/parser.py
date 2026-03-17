"""Extraction d'attributs structurés depuis une description normalisée."""

import re


def extract_attributes(description: str) -> dict:
    """Extrait les attributs détectables d'une description produit.

    Retourne un dict avec les clés trouvées:
    - size, color, material, format, thickness, dimension
    """
    attrs = {}
    lower = description.lower()

    # Taille
    size_match = re.search(r"\b(XS|S|M|L|XL|XXL|2XL|3XL)\b", description, re.IGNORECASE)
    if size_match:
        attrs["size"] = size_match.group(1).upper()
    # Tailles textuelles après normalisation
    for size_word, size_val in [("médium", "M"), ("medium", "M"), ("large", "L"),
                                 ("petit", "S"), ("xlarge", "XL"), ("x-large", "XL")]:
        if size_word in lower:
            attrs["size"] = size_val
            break

    # Couleur (inclut mauve)
    colors = ["blanc", "noir", "bleu", "jaune", "vert", "rouge", "gris", "orange", "mauve"]
    for c in colors:
        if c in lower:
            attrs["color"] = c
            break

    # Matière (pour gants, etc.)
    materials = ["nitrile", "latex", "vinyle", "vinyl", "polyéthylène", "coton", "cuir", "nylon"]
    for m in materials:
        if m in lower:
            attrs["material"] = m
            break

    # Épaisseur (pour gants: 4.5mil, 5mil, 8mil, etc.)
    thick_match = re.search(r"(\d+(?:\.\d+)?)\s*mil\b", lower)
    if thick_match:
        attrs["thickness"] = thick_match.group(1)

    # Dimensions (ex: 35x50, 42x48, 26x36)
    dim_match = re.search(r"(\d+)\s*[xX×]\s*(\d+)", description)
    if dim_match:
        attrs["dimension"] = f"{dim_match.group(1)}x{dim_match.group(2)}"

    # Format / conditionnement
    format_match = re.search(r"(\d+)\s*/\s*(\w+)", description)
    if format_match:
        attrs["format"] = format_match.group(0)

    # Taille en pouces (21", 24", 18 po)
    inch_match = re.search(r"(\d+)\s*(?:\"|''|po\b|pouces?\b)", lower)
    if inch_match:
        attrs["inch_size"] = inch_match.group(1)

    return attrs
