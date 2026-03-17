"""Lecture de fichiers Excel et CSV — clients et catalogues."""
from __future__ import annotations

import pandas as pd
from src.db.database import get_session
from src.db.models import Product
from src.normalization.cleaner import normalize_line


def read_client_file(filepath: str) -> list[dict]:
    """Lit un fichier Excel/CSV client et retourne les lignes produits.

    Chaque ligne retournée contient: description, quantity, uom.
    Le fichier doit avoir au minimum une colonne description.
    Détecte automatiquement les formats non-standard (ex: colonnes positionnelles).
    """
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    # Détecter le format non-standard (colonnes "Unnamed: X")
    unnamed_count = sum(1 for c in df.columns if str(c).startswith("Unnamed:"))
    if unnamed_count > len(df.columns) * 0.5:
        return _read_positional_format(filepath)

    # Normaliser les noms de colonnes
    df.columns = [c.strip().lower() for c in df.columns]

    # Trouver la colonne description (cherche des noms courants)
    desc_col = _find_column(df, ["description", "produit", "item", "article", "nom", "product"])
    qty_col = _find_column(df, ["quantité", "quantite", "qty", "qté", "qte"])
    uom_col = _find_column(df, ["unité", "unite", "uom", "um", "unit"])

    if desc_col is None:
        raise ValueError(
            f"Impossible de trouver une colonne description. "
            f"Colonnes trouvées: {list(df.columns)}"
        )

    lines = []
    for _, row in df.iterrows():
        desc = str(row[desc_col]).strip()
        if not desc or desc.lower() == "nan":
            continue
        lines.append({
            "description": desc,
            "quantity": _safe_float(row.get(qty_col)) if qty_col else None,
            "uom": str(row[uom_col]).strip() if uom_col and pd.notna(row.get(uom_col)) else None,
        })

    return lines


def _read_positional_format(filepath: str) -> list[dict]:
    """Lit un fichier Excel au format positionnel (colonnes sans en-tête standard).

    Détecte automatiquement les colonnes par leur contenu :
    - Colonne catégorie/utilité (texte descriptif court)
    - Colonne nom produit (texte descriptif long)
    - Colonne prix (numérique)
    """
    df = pd.read_excel(filepath, header=None)

    # Chercher la ligne d'en-tête réelle (celle qui contient des noms de colonnes
    # répartis sur plusieurs cellules, pas un titre fusionné)
    header_row = None
    for i, row in df.head(10).iterrows():
        non_null_values = [str(v).strip().upper() for v in row if pd.notna(v)]
        # Un header a au moins 3 cellules remplies (pas une ligne titre fusionnée)
        if len(non_null_values) < 3:
            continue
        joined = " ".join(non_null_values)
        header_kws = ["NOM PRODUIT", "DESCRIPTION", "PRODUIT", "PRIX",
                       "UTILIT", "CATÉGOR", "COMPARABLE", "QUANTIT"]
        matches = sum(1 for kw in header_kws if kw in joined)
        if matches >= 2:
            header_row = i
            break

    # Identifier les colonnes par position
    # Format BOD : col 0=catégorie, col 3=description, col 6=prix
    desc_col = None
    cat_col = None
    price_col = None

    if header_row is not None:
        for col_idx in range(len(df.columns)):
            val = str(df.iloc[header_row, col_idx]).strip().upper() if pd.notna(df.iloc[header_row, col_idx]) else ""
            if "NOM PRODUIT" in val or "DESCRIPTION" in val or "PRODUIT" in val:
                desc_col = col_idx
            elif "UTILIT" in val or "CATÉGOR" in val or "CATEGOR" in val:
                cat_col = col_idx
            elif val == "PRIX":
                price_col = col_idx

    # Fallback : deviner les colonnes par le contenu
    if desc_col is None:
        # La colonne description est celle avec le plus de texte non-vide
        text_counts = {}
        for col_idx in range(len(df.columns)):
            count = sum(1 for _, v in df[col_idx].items()
                       if pd.notna(v) and len(str(v).strip()) > 3)
            text_counts[col_idx] = count
        # Prendre la colonne avec le plus de texte (mais pas la première qui est souvent la catégorie)
        sorted_cols = sorted(text_counts.items(), key=lambda x: -x[1])
        if len(sorted_cols) >= 2:
            cat_col = sorted_cols[0][0]
            desc_col = sorted_cols[1][0]
        elif sorted_cols:
            desc_col = sorted_cols[0][0]

    if desc_col is None:
        raise ValueError("Impossible de détecter la colonne description dans le format positionnel")

    start_row = (header_row + 1) if header_row is not None else 0
    lines = []
    for i in range(start_row, len(df)):
        row = df.iloc[i]
        desc = str(row[desc_col]).strip() if pd.notna(row[desc_col]) else ""
        if not desc or desc.lower() in ("nan", ""):
            continue

        # Construire la description complète (catégorie + nom)
        cat = ""
        if cat_col is not None and pd.notna(row[cat_col]):
            cat = str(row[cat_col]).strip()

        # Toujours inclure la catégorie — elle donne le contexte produit
        # (ex: "NETTOYANT PLANCHER" + "NEUTRAL 500 PLUS 20L")
        if cat and cat.upper() not in desc.upper():
            full_desc = f"{cat} {desc}"
        else:
            full_desc = desc

        lines.append({
            "description": full_desc,
            "quantity": None,
            "uom": None,
        })

    return lines


def import_catalog(filepath: str) -> int:
    """Importe un catalogue produits (Excel/CSV) dans la base.

    Le fichier doit avoir au minimum: title ou description.
    Colonnes optionnelles: sku, brand, category, uom, price, case_qty.
    """
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    df.columns = [c.strip().lower() for c in df.columns]

    title_col = _find_column(df, ["item name", "title", "titre", "nom", "name", "produit", "item"])
    sku_col = _find_column(df, ["sku", "code", "internal_sku", "référence", "ref"])
    brand_col = _find_column(df, ["brand", "marque"])
    cat_col = _find_column(df, ["cf.catégorie", "cf.categorie", "category", "catégorie", "categorie", "cat"])
    uom_col = _find_column(df, ["usage unit", "uom", "unité", "unite", "um", "unit"])
    price_col = _find_column(df, ["rate", "price", "prix"])
    cost_col = _find_column(df, ["cf.cost price", "cost", "coût", "cout"])
    case_col = _find_column(df, ["case_qty", "caisse", "qty_caisse", "pack"])
    source_col = _find_column(df, ["source", "source_name", "fournisseur"])
    desc_col = _find_column(df, ["description"])
    item_id_col = _find_column(df, ["item id"])
    status_col = _find_column(df, ["status"])

    if title_col is None:
        raise ValueError(f"Colonne titre introuvable. Colonnes: {list(df.columns)}")

    session = get_session()
    count = 0
    skipped = 0
    try:
        for _, row in df.iterrows():
            # Ignorer les produits inactifs
            if status_col:
                status = _safe_str(row.get(status_col))
                if status and status.lower() != "active":
                    skipped += 1
                    continue

            title = str(row[title_col]).strip()
            if not title or title.lower() == "nan":
                continue

            # Extraire le prix (enlever "CAD " si présent)
            raw_price = _safe_str(row.get(price_col)) if price_col else None
            price = _parse_price(raw_price)

            # Coût fournisseur
            raw_cost = row.get(cost_col) if cost_col else None
            cost = _safe_float(raw_cost)

            # Description Zoho (ex: "48/Case") -> utile pour case_qty
            zoho_desc = _safe_str(row.get(desc_col)) if desc_col else None
            case_qty = _safe_int(row.get(case_col)) if case_col else None
            if not case_qty and zoho_desc:
                case_qty = _extract_case_qty(zoho_desc)

            product = Product(
                title=title,
                internal_sku=_safe_str(row.get(sku_col)) if sku_col else None,
                source_sku=_safe_str(row.get(item_id_col)) if item_id_col else None,
                brand=_safe_str(row.get(brand_col)) if brand_col else None,
                category=_normalize_category(_safe_str(row.get(cat_col))) if cat_col else "autre",
                uom=_safe_str(row.get(uom_col)) if uom_col else None,
                price=price,
                case_qty=case_qty,
                description=zoho_desc,
                source_name=_safe_str(row.get(source_col)) if source_col else "zoho",
                normalized_description=normalize_line(title),
                is_active=True,
            )
            session.add(product)
            count += 1

        session.commit()
        if skipped:
            print(f"  ({skipped} produits inactifs ignorés)")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return count


def _parse_price(val: str | None) -> float | None:
    """Parse un prix Zoho (ex: 'CAD 12.99' -> 12.99)."""
    if not val:
        return None
    import re
    cleaned = re.sub(r"[A-Za-z$€£\s]", "", val.replace(",", "."))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_case_qty(desc: str) -> int | None:
    """Extrait la quantité par caisse d'une description Zoho (ex: '48/Case' -> 48)."""
    import re
    match = re.match(r"(\d+)\s*/\s*(?:case|caisse|cs|bte|box)", desc, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


# Mapping des catégories Zoho vers nos catégories internes
_CATEGORY_MAP = {
    # Chimique / nettoyant
    "produit nettoyant": "chimique",
    "produits nettoyants": "chimique",
    "produit chimique": "chimique",
    "nettoyant": "chimique",
    "chimique": "chimique",
    "chemical": "chimique",
    # Papier
    "produit papier": "papier",
    "produits papier": "papier",
    "papier": "papier",
    "serviette": "papier",
    # EPI
    "epi": "epi",
    "gants": "epi",
    "masque / mask": "epi",
    "masque": "epi",
    "équipement de protection": "epi",
    "protection individuelle": "epi",
    "culotte": "epi",
    "culotte pull-up": "epi",
    "incontinence": "epi",
    # Sacs
    "sac déchet": "sacs",
    "sac déchets": "sacs",
    "sac à déchets": "sacs",
    "sac a déchets": "sacs",
    "sac poubelle": "sacs",
    "sac poubelle - garbage bags": "sacs",
    "produit déchet": "sacs",
    "sac": "sacs",
    "sacs": "sacs",
    # Emballage
    "produit emballage": "emballage",
    "emballage": "emballage",
    # Industriel / entretien
    "industriel": "entretien",
    "produit industriel": "entretien",
    "entretien": "entretien",
}


def _normalize_category(raw: str | None) -> str:
    """Convertit une catégorie Zoho vers notre catégorie interne."""
    if not raw:
        return "autre"
    lower = raw.strip().lower()
    # Match exact
    if lower in _CATEGORY_MAP:
        return _CATEGORY_MAP[lower]
    # Match partiel (clé contenue dans la valeur ou inverse)
    for key, cat in _CATEGORY_MAP.items():
        if key in lower or lower in key:
            return cat
    return "autre"


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Trouve la première colonne qui correspond à un des noms candidats.

    Priorité 1: match exact (colonne == candidat)
    Priorité 2: le candidat est contenu dans le nom de colonne
    """
    # Pass 1: match exact
    for candidate in candidates:
        for col in df.columns:
            if col == candidate:
                return col

    # Pass 2: match partiel (candidat contenu dans le nom de colonne)
    for candidate in candidates:
        for col in df.columns:
            if candidate in col and col != candidate:
                return col

    return None


def _safe_float(val) -> float | None:
    try:
        if pd.isna(val):
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    try:
        if pd.isna(val):
            return None
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_str(val) -> str | None:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    return s if s and s.lower() != "nan" else None
