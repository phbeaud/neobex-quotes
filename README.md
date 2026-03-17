# Neobex Quotes

Outil local de préparation de soumissions pour Neobex.
Lit une demande client, fait le matching produit, et prépare une soumission structurée.

## Installation

```bash
cd ~/neobex_quotes
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Commandes

```bash
# Initialiser la base de données
python -m src.main init-db

# Importer un catalogue produits
python -m src.main import-products data/catalogs/catalogue.xlsx

# Analyser une demande client
python -m src.main analyze data/raw/liste_client.xlsx

# Exporter le fichier de revue
python -m src.main review-export 1

# Finaliser après validation
python -m src.main finalize exports/revue_1.xlsx 1
```

## Structure

```
src/
  ingestion/     — lecture Excel, CSV, PDF, texte
  normalization/ — nettoyage descriptions, catégories
  matching/      — moteur de matching (exact, fuzzy, règles)
  outputs/       — exports Excel (revue + final)
  db/            — modèles SQLite, accès données
  zoho/          — intégration Zoho Invoice (Phase 2)
```

## Pipeline

1. Lecture fichier client
2. Extraction lignes produits
3. Normalisation descriptions
4. Détection catégories
5. Matching contre catalogue interne
6. Génération fichier de revue Excel
7. Validation humaine
8. Export final / push Zoho Invoice
