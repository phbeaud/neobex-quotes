"""Nettoyage et normalisation des descriptions produits."""
from __future__ import annotations

import re

# Mapping tailles courantes
SIZE_MAP = {
    "xs": "XS", "extra-small": "XS", "très petit": "XS", "x-small": "XS",
    "s": "S", "small": "S", "petit": "S", "p": "S",
    "m": "M", "medium": "M", "moyen": "M", "med": "M", "médium": "M",
    "l": "L", "large": "L", "grand": "L", "g": "L",
    "xl": "XL", "extra-large": "XL", "très grand": "XL", "tg": "XL", "xlarge": "XL", "x-large": "XL",
    "xxl": "XXL", "2xl": "XXL",
}

# Mapping couleurs
COLOR_MAP = {
    "blc": "blanc", "wht": "blanc", "white": "blanc", "blancs": "blanc",
    "nr": "noir", "blk": "noir", "black": "noir", "noirs": "noir",
    "bl": "bleu", "blue": "bleu", "bleus": "bleu",
    "jne": "jaune", "yellow": "jaune",
    "vrt": "vert", "green": "vert",
    "rge": "rouge", "red": "rouge", "rouges": "rouge",
    "mauve": "mauve", "purple": "mauve",
    "gris": "gris", "grey": "gris", "gray": "gris",
    "orange": "orange",
}

# Synonymes métier — normalise les termes courants vers une forme unique
SYNONYM_MAP = {
    # Sacs
    "sac poubelle": "sac ordures",
    "sac à poubelle": "sac ordures",
    "sac à ordures": "sac ordures",
    "sac déchet": "sac ordures",
    "sac à déchets": "sac ordures",
    "sac a déchets": "sac ordures",
    "garbage bag": "sac ordures",
    "can liner": "sac ordures",
    "trash bag": "sac ordures",
    "refuse bag": "sac ordures",
    # Papier
    "papier à main": "essuie-mains",
    "papier à mains": "essuie-mains",
    "papier main": "essuie-mains",
    "papier mains": "essuie-mains",
    "hand paper": "essuie-mains",
    "hand towel": "essuie-mains",
    "paper towel": "essuie-mains",
    "paper towel rolls": "essuie-mains rouleau",
    "papier hygiène": "papier hygiénique",
    "papier toilette": "papier hygiénique",
    "toilet paper": "papier hygiénique",
    "bath tissue": "papier hygiénique",
    "bathroom tissue": "papier hygiénique",
    "jrt toilet paper": "papier hygiénique jumbo",
    "jumbo roll": "rouleau jumbo",
    "facial tissue": "papier mouchoir",
    "mouchoir": "papier mouchoir",
    # Gants
    "gant nitrile": "gant nitrile",
    "gants de nitrile": "gant nitrile",
    "gants en nitrile": "gant nitrile",
    "gant en nitrile": "gant nitrile",
    "gant d'examen en nitrile": "gant nitrile examen",
    "gants d'examen en nitrile": "gant nitrile examen",
    "gant d'examen nitrile": "gant nitrile examen",
    "nitrile examination gloves": "gant nitrile examen",
    "nitrile exam gloves": "gant nitrile examen",
    "nitrile disposable gloves": "gant nitrile jetable",
    "gant vinyle": "gant vinyle",
    "gants vinyle": "gant vinyle",
    "gants en vinyle": "gant vinyle",
    "vinyl examination gloves": "gant vinyle examen",
    "vinyl gloves": "gant vinyle",
    "gant latex": "gant latex",
    "gants latex": "gant latex",
    "latex examination gloves": "gant latex examen",
    "latex gloves": "gant latex",
    "poly disposable gloves": "gant poly jetable",
    "gant poly": "gant poly jetable",
    "string knit gloves": "gant tricot",
    "gant de travail": "gant travail",
    "work gloves": "gant travail",
    "examination gloves": "gant examen",
    # Épaisseurs gants (normaliser mil/mm)
    "5mm": "5mil",
    "4.5mm": "4.5mil",
    "4,5 mil": "4.5mil",
    "4,5mil": "4.5mil",
    "5 mil": "5mil",
    "3 mil": "3mil",
    "6 mil": "6mil",
    "8 mil": "8mil",
    # Filets / couvre-chef
    "filet à barbe": "filet barbe",
    "filets à barbe": "filet barbe",
    "couvre-barbe": "filet barbe",
    "beard net": "filet barbe",
    "beard cover": "filet barbe",
    "filet à cheveux": "filet cheveux",
    "filets à cheveux": "filet cheveux",
    "couvre-cheveux": "filet cheveux",
    "hairnet": "filet cheveux",
    "hair cover": "filet cheveux",
    "hair net": "filet cheveux",
    "bouffant cap": "bonnet bouffant",
    "bonnet bouffant": "bonnet bouffant",
    "shoe cover": "couvre-chaussure",
    "couvre-chaussure": "couvre-chaussure",
    "couvre-soulier": "couvre-chaussure",
    "boot cover": "couvre-botte",
    "couvre-botte": "couvre-botte",
    # Combinaisons / protection corporelle
    "coverall": "combinaison",
    "combinaison": "combinaison",
    "coveralls": "combinaison",
    "lab coat": "sarrau",
    "sarrau": "sarrau",
    "jaquette": "sarrau",
    "sleeve cover": "manchon",
    "arm sleeve": "manchon",
    "manchon": "manchon",
    # Masques
    "face mask": "masque",
    "surgical mask": "masque chirurgical",
    "masque chirurgical": "masque chirurgical",
    "masque procédure": "masque procédure",
    "procedure mask": "masque procédure",
    # Tabliers
    "apron": "tablier",
    "tablier": "tablier",
    "poly apron": "tablier poly",
    "tablier poly": "tablier poly",
    # Nettoyants
    "nettoyant neutre": "nettoyant neutre",
    "nettoyant à plancher": "nettoyant plancher",
    "nettoyant planchers": "nettoyant plancher",
    "floor cleaner": "nettoyant plancher",
    "all purpose cleaner": "nettoyant tout usage",
    "nettoyant tout usage": "nettoyant tout usage",
    "degreaser": "dégraissant",
    "dégraissant": "dégraissant",
    "hand soap": "savon mains",
    "savon à mains": "savon mains",
    "savon mains": "savon mains",
    "hand sanitizer": "désinfectant mains",
    "désinfectant à mains": "désinfectant mains",
    # Emballage alimentaire
    "aluminum foil": "papier aluminium",
    "papier aluminium": "papier aluminium",
    "plastic wrap": "pellicule plastique",
    "pellicule plastique": "pellicule plastique",
    "food container": "contenant alimentaire",
    "contenant alimentaire": "contenant alimentaire",
    # Buanderie / lessive
    "assouplissant neutralisant lessive": "assouplissant lessive",
    "buanderie detergent": "détergent buanderie",
    "détachant lessive": "détachant lessive",
    # Lave-vaisselle
    "détergent lave-vaisselle": "détergent lave-vaisselle",
    "detergent lave-vaisselle": "détergent lave-vaisselle",
    "detergent lave vaisselle": "détergent lave-vaisselle",
    "agent rincage lave-vaisselle": "agent rinçage lave-vaisselle",
    "agent rinçage lave-vaisselle": "agent rinçage lave-vaisselle",
    "detartrant lave vaisselle": "détartrant lave-vaisselle",
    "détartrant lave vaisselle": "détartrant lave-vaisselle",
    "agent trempage": "agent trempage",
    # Nettoyants spécifiques
    "nettoyant concentre salle bain": "nettoyant salle de bain",
    "nettoyant salle bain": "nettoyant salle de bain",
    "nettoyant en creme": "nettoyant crème abrasif",
    "nettoyant grill four friteuse": "nettoyant gril friteuse",
    "dégraisseur tout usage": "dégraissant tout usage",
    "dégraisseur tout usage cuisine": "dégraissant cuisine",
    "detergent chaudrons": "détergent chaudrons",
    # Désinfectants
    "désinfectant neutre désodorisant": "désinfectant neutre",
    "désodorisant floral": "désodorisant",
    "lingette désinfectante": "lingette désinfectante",
    "désinfectant moussant alcool": "désinfectant alcool",
    # Papier abréviations
    "papier hyg": "papier hygiénique",
    "papier main": "essuie-mains",
    # Savons
    "savon-mousse main et corp": "savon mousse mains corps",
    "savon mousse": "savon mousse",
    # Mesures
    "extra-fort": "extra fort",
    "extra fort": "extra fort",
    "x-strong": "extra fort",
    "ex-strong": "extra fort",
    "extra-strong": "extra fort",
    "heavy duty": "robuste",
    "robuste": "robuste",
    "regular": "régulier",
    "régulier": "régulier",
}

# Mapping unités
UOM_MAP = {
    "cs": "caisse", "cse": "caisse", "case": "caisse", "bte": "boîte", "box": "boîte",
    "pqt": "paquet", "pkg": "paquet", "pack": "paquet",
    "rl": "rouleau", "roll": "rouleau",
    "pr": "paire", "pair": "paire",
    "ea": "unité", "each": "unité", "un": "unité", "pc": "unité", "pce": "unité",
}


def normalize_line(text: str) -> str:
    """Normalise une description produit."""
    if not text:
        return ""

    t = text.lower().strip()

    # Retirer les mots-bruit génériques (préfixes de catégorie non-informatifs)
    t = _remove_noise_words(t)

    # Garder seulement la partie française (avant le "/" séparateur FR/EN)
    t = _extract_french_part(t)

    # Retirer les caractères spéciaux inutiles
    t = re.sub(r"[\"'`]", "", t)
    t = re.sub(r"\s+", " ", t)

    # Normaliser les dimensions de sacs AVANT de retirer les codes
    # (ex: "22x24" -> "sac ordures 22 x 24")
    t = _normalize_sac_dimensions(t)

    # Retirer les codes produits concurrents (ex: "AR-2000", "BD-3", "SC-1000")
    t = _remove_product_codes(t)

    # Normaliser les tailles (APRÈS sacs pour ne pas convertir "xs"=extra-fort)
    t = _normalize_sizes(t)

    # Normaliser les couleurs
    t = _normalize_colors(t)

    # Normaliser les formats de caisse (ex: "12/cs", "24/caisse")
    t = _normalize_case_format(t)

    # Appliquer les synonymes métier
    t = _apply_synonyms(t)

    # Retirer la ponctuation résiduelle (tirets, virgules isolées, etc.)
    t = re.sub(r"[–—,;:()]", " ", t)
    t = re.sub(r"\s+", " ", t)

    # Retirer les doublons de mots consécutifs
    t = re.sub(r"\b(\w+)\s+\1\b", r"\1", t)

    return t.strip()


def _remove_noise_words(text: str) -> str:
    """Retire les mots-bruit qui n'apportent pas d'information pour le matching."""
    noise = [
        "accessoire", "acessoire", "produit", "article",
    ]
    words = text.split()
    cleaned = [w for w in words if w not in noise]
    return " ".join(cleaned) if cleaned else text


def _remove_product_codes(text: str) -> str:
    """Retire les codes produits concurrents qui polluent le matching fuzzy.

    Exemples: "AR-2000", "BD-3", "SC-1000", "BV-5", "NSB-820", "CUV-800"
    Ne touche PAS aux dimensions de sacs (déjà normalisées en "22 x 24").
    """
    words = text.split()
    # Ne pas retirer si la description est trop courte (juste un code)
    if len(words) <= 2:
        return text

    # Retirer les codes alphanumériques de type "XX-1234", "BP-8", "BD-3"
    cleaned = re.sub(r"\b[a-z]{1,5}-\d{1,5}[a-z]{0,2}\b", "", text)
    # Retirer les codes sans tiret type "NSB820", "CUV800" (2+ lettres + 3+ chiffres)
    cleaned = re.sub(r"\b[a-z]{2,5}\d{3,5}\b", "", cleaned)
    # Retirer les codes type "4x4l", "2x4l", "6x800ml" (conditionnement, pas dimensions sacs)
    cleaned = re.sub(r"\b\d+x\d+[a-z]{1,3}\b", "", cleaned)
    # Retirer les volumes isolés "20l", "4l"
    cleaned = re.sub(r"\b\d+l\b", "", cleaned)
    # Retirer les pourcentages isolés "6%"
    cleaned = re.sub(r"\b\d+%", "", cleaned)
    # Retirer quantités isolées type "500", "150", "100" en fin de ligne
    cleaned = re.sub(r"\s+\d{2,4}\s*$", "", cleaned)
    # Nettoyer
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Si tout a été retiré, garder l'original
    return cleaned if len(cleaned) > 3 else text


def _normalize_sac_dimensions(text: str) -> str:
    """Normalise les dimensions de sacs pour matcher le format catalogue.

    "22x24 noir reg" -> "sac ordures 22 x 24 noir régulier"
    "35x50 xs noir" -> "sac ordures 35 x 50 extra fort noir"
    """
    # Pattern: dimensions NNxNN au début ou après "sac"
    match = re.search(r"\b(\d{2})x(\d{2})\b", text)
    if not match:
        return text

    dim1, dim2 = match.group(1), match.group(2)
    # Vérifier que c'est bien une dimension de sac (pas une microfibre 14x14)
    dim_total = int(dim1) + int(dim2)
    if dim_total < 40:  # Trop petit pour un sac (ex: 14x14 microfibre)
        return text

    # Normaliser le format de dimension
    text = re.sub(r"\b(\d{2})x(\d{2})\b", r"\1 x \2", text)

    # Ajouter "sac ordures" si pas déjà présent
    if "sac" not in text:
        text = "sac ordures " + text

    # Normaliser les forces
    text = re.sub(r"\breg\b", "régulier", text)
    text = re.sub(r"\bxs\b", "extra fort", text, flags=re.IGNORECASE)
    text = re.sub(r"\bxxs\b", "extra extra fort", text, flags=re.IGNORECASE)

    return text


def _normalize_sizes(text: str) -> str:
    words = text.split()
    result = []
    for w in words:
        clean = w.strip(".,;:()")
        if clean.lower() in SIZE_MAP:
            result.append(SIZE_MAP[clean.lower()])
        else:
            result.append(w)
    return " ".join(result)


def _normalize_colors(text: str) -> str:
    words = text.split()
    result = []
    for w in words:
        clean = w.strip(".,;:()")
        if clean.lower() in COLOR_MAP:
            result.append(COLOR_MAP[clean.lower()])
        else:
            result.append(w)
    return " ".join(result)


def _normalize_case_format(text: str) -> str:
    """Normalise les formats de conditionnement (ex: '12/cs' -> '12/caisse')."""
    def replace_uom(match):
        qty = match.group(1)
        unit = match.group(2).lower()
        normalized = UOM_MAP.get(unit, unit)
        return f"{qty}/{normalized}"

    return re.sub(r"(\d+)\s*/\s*(\w+)", replace_uom, text)


def _apply_synonyms(text: str) -> str:
    """Remplace les synonymes métier par leur forme normalisée.

    Applique les remplacements du plus long au plus court
    pour éviter les conflits partiels.
    """
    result = text
    # Trier par longueur décroissante pour matcher les expressions longues d'abord
    for source, target in sorted(SYNONYM_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if source in result:
            result = result.replace(source, target)
    return result


def _extract_french_part(text: str) -> str:
    """Extrait la partie française d'une description bilingue FR/EN.

    Les produits Zoho sont souvent au format:
    'Filets à barbe blancs – 18 po /SoftCover Beard Nets White 18"'
    On garde seulement la partie avant le '/' séparateur.
    """
    if "/" not in text:
        return text

    # Chercher un "/" qui sépare FR et EN (pas un "/" dans "48/caisse")
    # Heuristique: le "/" séparateur est entouré d'espaces ou précédé d'une mesure
    parts = re.split(r"\s+/\s*|\s*/\s+", text)
    if len(parts) >= 2:
        fr_part = parts[0].strip()
        # Vérifier que c'est bien un séparateur FR/EN (la partie après contient de l'anglais)
        en_part = parts[1].strip().lower()
        en_markers = ["the", "for", "and", "with", "white", "black", "blue",
                       "red", "green", "yellow", "large", "medium", "small",
                       "hair", "beard", "glove", "bag", "paper", "towel",
                       "soap", "cleaner", "roll", "sheet", "cover", "net"]
        if any(m in en_part for m in en_markers) or not fr_part:
            return fr_part if fr_part else text

    return text


def extract_quantity_from_description(text: str) -> tuple[str, float | None, str | None]:
    """Tente d'extraire une quantité et unité intégrées dans la description.

    Retourne (description nettoyée, quantité, unité).
    """
    # Pattern: "12 caisses de gants" ou "caisse de 24"
    match = re.search(r"(\d+)\s*(caisses?|boîtes?|paquets?|rouleaux?|paires?)", text, re.IGNORECASE)
    if match:
        qty = float(match.group(1))
        uom = match.group(2).lower()
        cleaned = text[:match.start()].strip() + " " + text[match.end():].strip()
        return cleaned.strip(), qty, uom

    return text, None, None
