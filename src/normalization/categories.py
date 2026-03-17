"""Détection de catégorie produit à partir de la description."""

# Mots-clés par catégorie
CATEGORY_KEYWORDS = {
    "epi": [
        "gant", "gants", "lunette", "lunettes", "casque", "bouchon", "protection",
        "visière", "sarrau", "combinaison", "masque", "respirateur", "harnais",
        "botte", "bottes", "chaussure", "sécurité", "nitrile", "latex", "vinyle",
        "filet", "filets", "barbe", "cheveux", "couvre-barbe", "couvre-cheveux",
        "hairnet", "beard", "culotte", "incontinence", "tablier", "jaquette",
        "neoprene", "coverall", "glove", "apron",
    ],
    "papier": [
        "papier", "essuie", "serviette", "mouchoir", "rouleau", "tissue",
        "hygiénique", "main", "pli", "feuille", "distributeur",
        "paper towel", "toilet paper", "bath tissue", "tork",
        "privilege", "scott",
    ],
    "chimique": [
        "désinfectant", "nettoyant", "savon", "dégraissant", "javellisant",
        "détergent", "assainisseur", "chlore", "alcool", "peroxyde",
        "germicide", "antibactérien",
        "detergent", "assouplissant", "détachant", "rinçage", "rincage",
        "lave-vaisselle", "detartrant", "détartrant", "trempage",
        "lingette", "désodorisant", "nettoyant plancher",
        "mousse", "foam", "sanitizer", "cleaner", "degreaser",
        "neutra-quat", "vaporisateur",
    ],
    "sacs": [
        "sac", "sacs", "poubelle", "ordure", "récupération", "recyclage",
        "compost", "liner", "garbage", "bag",
    ],
    "emballage": [
        "pellicule", "stretch", "film", "étirable", "ruban", "adhésif",
        "palette", "boîte", "carton",
    ],
    "entretien": [
        "balai", "vadrouille", "moppe", "seau", "chiffon", "éponge",
        "raclette", "brosse", "plumeau", "poussière",
        "microfibre", "ratine", "guenille", "tampon", "scotch brite",
        "tete de moppe",
    ],
}

# Patterns de dimensions typiques des sacs (ex: "22x24", "35x50")
import re
_SAC_DIMENSION_PATTERN = re.compile(r"\b\d{2}x\d{2}\b")


def detect_category(description: str) -> str:
    """Détecte la catégorie la plus probable pour une description normalisée."""
    if not description:
        return "autre"

    lower = description.lower()
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[category] = score

    # Bonus: dimensions typiques de sacs (22x24, 35x50, 26x36, 42x48)
    if _SAC_DIMENSION_PATTERN.search(lower):
        scores["sacs"] = scores.get("sacs", 0) + 2

    if not scores:
        return "autre"

    return max(scores, key=scores.get)
