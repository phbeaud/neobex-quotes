"""Produits populaires à ajouter aux soumissions.

Basé sur l'analyse de 311 pages / 1561 occurrences de soumissions Neobex.
Classé par fréquence réelle d'apparition dans les devis.
"""
from __future__ import annotations

# Catégories de produits populaires avec SKU et description courte
# "default": True = coché par défaut dans l'interface
# Fréquence entre parenthèses = nb d'apparitions dans les soumissions analysées
POPULAR_PRODUCTS: dict[str, list[dict]] = {
    "🧤 Gants": [
        {"sku": "ANBM10014", "label": "Gant Nitrile AdvanCare 3,5 mil (100/bte)", "default": True},       # 73x
        {"sku": "11311-11321-11331-11341", "label": "Gant Nitrile Bleu TouchFlex 4,5 mil (100/bte)"},      # 33x
        {"sku": "1560", "label": "Gant Vinyle Synthétique Neobex (100/bte)"},                               # 29x
        {"sku": "1545", "label": "Gant Nitrile Neobex 5 mil (100/bte)"},                                    # 23x
        {"sku": "11311B", "label": "Gant Nitrile Noir TouchFlex 4,5 mil (100/bte)"},                        # 12x
        {"sku": "Z1100503B", "label": "Gants nitrile travaux Neobex (100/bte)"},                             # 10x
    ],
    "😷 Masques & Protection": [
        {"sku": "intco3l5040", "label": "Masque 3 plis Intco Niveau 3", "default": True},                   # 27x
        {"sku": "FE035C", "label": "Bouchons d'oreilles mousse cordés (100 paires)"},                       # 12x
        {"sku": "CSKN95", "label": "Masques KN95 Clean Shield"},                                             # 7x
        {"sku": "FE035NC", "label": "Bouchons d'oreilles mousse sans cordon (200 paires)"},                  # 7x
    ],
    "🧻 Papier": [
        {"sku": "SNS-48420", "label": "Papier hygiénique EVEREST 2 plis 420f (48/cs)", "default": True},    # 25x
        {"sku": "INS-ts-ft100", "label": "Mouchoirs 30x100 feuilles"},                                      # 22x
        {"sku": "SNS-HWT800K", "label": "Essuie-mains brun/kraft 800' (6/cs)", "default": True},            # 10x
        {"sku": "SNS-HWT800W", "label": "Essuie-mains blanc 800' (6/cs)"},                                  # 10x
        {"sku": "INS-TS-350KRT", "label": "Essuie-mains kraft 12x350' (12/cs)"},                            # 10x
        {"sku": "SNS-48500", "label": "Papier hygiénique EVEREST 2 plis 500f (48/cs)"},                     # 9x
        {"sku": "MFC1616B", "label": "Chiffon microfibre bleu 16x16"},                                      # 8x
    ],
    "🗑️ Sacs à déchets": [
        {"sku": "INS-gb-2224", "label": "Sacs 22x24 noirs (500/cs)"},                                       # 21x
        {"sku": "INS-gb-3550s", "label": "Sacs 35x50 forts noirs (125/cs)"},                                # 20x
        {"sku": "INS-gb-3550xs", "label": "Sacs 35x50 extra-forts noirs (100/cs)", "default": True},        # 17x
        {"sku": "INS-gb-2636xs", "label": "Sacs 26x36 extra-forts (150/cs)"},                               # 13x
        {"sku": "INS-gb-2636r", "label": "Sacs 26x36 réguliers (250/cs)"},                                  # 11x
        {"sku": "INS-gb-2636s", "label": "Sacs 26x36 forts (200/cs)"},                                      # 10x
        {"sku": "INS-gb-2022", "label": "Sacs 20x22 noirs (500/cs)"},                                       # 10x
        {"sku": "INS-gb-3038s", "label": "Sacs 30x38 forts noirs (150/cs)"},                                # 10x
        {"sku": "INS-GB-4248XS", "label": "Sacs 42x48 extra-forts noirs"},                                  # 8x
        {"sku": "BJI-4248BLXST", "label": "Sacs 42x48 extra-forts noirs BJI"},                              # 8x
    ],
    "🧹 Entretien": [
        {"sku": "SP69-M", "label": "Tampons à récurer verts 6x9 (100/bte)"},                                # 14x
        {"sku": "INS-AC-WM-20BL", "label": "Vadrouille humide 20 oz"},                                      # 9x
        {"sku": "25000P", "label": "Tampon à récurer 6x9 (100/bte)"},                                       # 8x
        {"sku": "ADV-110542", "label": "Vaporisateur robuste"},                                              # 7x
        {"sku": "INO-va924b", "label": "Bouteille graduée 750ml"},
    ],
    "🧪 Chimique": [
        {"sku": "INO-KL12-4", "label": "KLEEN 12 Nettoyant vitres 4L"},                                     # 20x
        {"sku": "INO-de5-4", "label": "DERM 5 Savon à mains 4L"},                                           # 11x
        {"sku": "INO-ba8-4", "label": "BANO 8 Nettoyant cuvette acide 4L"},                                 # 10x
        {"sku": "INS-SF-GOON-4", "label": "Dégraissant Goon 4L"},                                           # 9x
        {"sku": "LAV-044015", "label": "Javel LAVO PRO 6% (3,6L)"},                                         # 9x
        {"sku": "INO-SHP10-4", "label": "SHOP 10 Dégraissant concentré 4L"},                                # 9x
        {"sku": "INO-ba1-4", "label": "BANO 1 Nettoyant salle de bain 4L"},                                 # 9x
        {"sku": "INO-gl12-20", "label": "GLOSS 12 Nettoyant planchers 20L"},                                # 8x
        {"sku": "INO-ww30-20", "label": "CHEF 30 Assainisseur lave-vaisselle 20L"},                         # 8x
        {"sku": "INO-gl12-4", "label": "GLOSS 12 Nettoyant planchers 4L"},                                  # 8x
        {"sku": "INO-MED2-500", "label": "Désinfectant mains MED 2 (500ml)"},
    ],
    "👷 EPI": [
        {"sku": "NFBCW21", "label": "Filet à cheveux plat blanc 21\" (1000/cs)", "default": True},          # 23x
        {"sku": "NPBRCW18", "label": "Couvre-barbe plissé blanc 18\" (1000/cs)"},                            # 21x
        {"sku": "NPBCW21", "label": "Filet à cheveux plissé blanc 21\" (1000/cs)"},                          # 21x
        {"sku": "NFBCW24", "label": "Filet à cheveux plat blanc 24\" (1000/cs)"},                            # 12x
        {"sku": "1287", "label": "CaviWipes Lingettes désinfectantes"},                                      # 12x
        {"sku": "CPESC40B", "label": "Couvre-chaussures CPE vierge (1000/cs)"},                              # 11x
        {"sku": "NPBCW24", "label": "Filet à cheveux plissé blanc 24\" (1000/cs)"},                          # 9x
        {"sku": "TPUA60W", "label": "Tablier réutilisable TPU 35x45\" (6/cs)"},                             # 9x
        {"sku": "NRBRCW18", "label": "Couvre-barbe régulier blanc 18\" (1000/cs)"},                          # 9x
        {"sku": "NMHC21-BL", "label": "Filet à cheveux maille nylon noir 21\" (1000/cs)"},                  # 8x
        {"sku": "PEA15-W", "label": "Tablier polyéthylène 1,5 mil 28x46\" (100/cs)"},                       # 8x
        {"sku": "PES07516B", "label": "Manchons PE bleus 16\" 0,75 mil (2000/cs)"},                         # 7x
        {"sku": "BHW", "label": "Cagoule de protection blanche (500/cs)"},                                   # 7x
        {"sku": "PPSC45B", "label": "Couvre-chaussures antidérapants bleus"},                                # 7x
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
