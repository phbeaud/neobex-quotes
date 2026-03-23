"""Produits populaires à ajouter aux soumissions.

Basé sur l'analyse de 60 pages de soumissions Neobex.
Ces produits sont fréquemment ajoutés même quand le client
ne les demande pas explicitement.
"""
from __future__ import annotations

# Catégories de produits populaires avec SKU et description courte
POPULAR_PRODUCTS: dict[str, list[dict]] = {
    "🧤 Gants": [
        {"sku": "ANBM10014", "label": "Gant Nitrile AdvanCare 3,5 mil (100/bte)", "default": True},
        {"sku": "11311B 11321B 11331B 11341B", "label": "Gant Nitrile Noir TouchFlex 4,5 mil (100/bte)"},
        {"sku": "VGPF3001", "label": "Gant Vinyle Synthétique (100/bte)"},
        {"sku": "intco3l5040", "label": "Masque 3 plis Intco Niveau 3"},
    ],
    "🧻 Papier": [
        {"sku": "SNS-48420", "label": "Papier hygiénique EVEREST 2 plis 420f (48/cs)", "default": True},
        {"sku": "INS-ts-500tt", "label": "Papier hygiénique 2 plis 500f (48/cs)"},
        {"sku": "SNS-HWT800K", "label": "Essuie-mains brun/kraft (6/cs)", "default": True},
        {"sku": "SNS-HWT800W", "label": "Essuie-mains blanc (6/cs)"},
        {"sku": "INS-ts-ft100", "label": "Mouchoirs 30x100 feuilles"},
        {"sku": "FSW1124B", "label": "Chiffon J 24x13"},
    ],
    "🗑️ Sacs à déchets": [
        {"sku": "INS-gb-2224", "label": "Sacs 22x24 noirs (500/cs)"},
        {"sku": "INS-gb-2636xs", "label": "Sacs 26x36 extra-forts (150/cs)", "default": True},
        {"sku": "INS-gb-2636r", "label": "Sacs 26x36 réguliers (250/cs)"},
        {"sku": "INS-gb-2636s", "label": "Sacs 26x36 forts (200/cs)"},
        {"sku": "INS-gb-3550xs", "label": "Sacs 35x50 extra-forts noirs (100/cs)"},
        {"sku": "INS-gb-3550xsc", "label": "Sacs 35x50 extra-forts clairs (125/cs)"},
    ],
    "🧹 Entretien": [
        {"sku": "SP69-M", "label": "Tampons à récurer verts 6x9 (100/bte)"},
        {"sku": "INS-AC-WM-20BL", "label": "Vadrouille humide 20 oz"},
        {"sku": "ADV-110542", "label": "Vaporisateur robuste"},
        {"sku": "INO-va924b", "label": "Bouteille graduée 750ml"},
    ],
    "🧪 Chimique": [
        {"sku": "INO-KL6-4", "label": "KLEEN 6 Dégraissant tout usage 4L"},
        {"sku": "INS-SF-GOON-4", "label": "Dégraissant Goon 4L"},
        {"sku": "INO-MED2-500", "label": "Désinfectant mains MED 2 (500ml)", "default": True},
        {"sku": "LAV-044015", "label": "Javel LAVO PRO 6% (3,6L)"},
        {"sku": "INO-gl12-20", "label": "GLOSS 12 Nettoyant planchers 20L"},
        {"sku": "INO-ww30-20", "label": "CHEF 30 Assainisseur lave-vaisselle 20L"},
    ],
    "👷 EPI": [
        {"sku": "NPBCW21", "label": "Filet à cheveux plissé blanc 21\" (1000/cs)"},
        {"sku": "NFBCW21", "label": "Filet à cheveux plat blanc 21\" (1000/cs)"},
        {"sku": "NPBRCW18", "label": "Couvre-barbe plissé blanc 18\" (1000/cs)"},
        {"sku": "NMBC18BL", "label": "Filet à barbe maille nylon noir (1000/cs)"},
    ],
}


def get_popular_skus() -> list[str]:
    """Retourne la liste de tous les SKU populaires."""
    skus = []
    for category, products in POPULAR_PRODUCTS.items():
        for p in products:
            skus.append(p["sku"])
    return skus


def get_default_skus() -> list[str]:
    """Retourne les SKU cochés par défaut."""
    return [
        p["sku"]
        for products in POPULAR_PRODUCTS.values()
        for p in products
        if p.get("default")
    ]
