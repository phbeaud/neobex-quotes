"""Lecture de fichiers PDF (factures, listes fournisseurs)."""
from __future__ import annotations

import pdfplumber


def read_pdf_file(filepath: str) -> list[dict]:
    """Extrait les lignes produits d'un PDF.

    Tente d'abord l'extraction de tableaux, sinon extrait le texte brut.
    """
    lines = []

    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            # Essayer d'extraire des tableaux
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    lines.extend(_parse_table(table))
            else:
                # Fallback: texte brut
                text = page.extract_text()
                if text:
                    from src.ingestion.text_reader import parse_text
                    lines.extend(parse_text(text))

    return lines


def _parse_table(table: list[list]) -> list[dict]:
    """Parse un tableau PDF extrait par pdfplumber."""
    if not table or len(table) < 2:
        return []

    # La première ligne est probablement l'en-tête
    headers = [str(h).strip().lower() if h else "" for h in table[0]]

    desc_idx = _find_index(headers, ["description", "produit", "item", "article", "nom"])
    qty_idx = _find_index(headers, ["quantité", "quantite", "qty", "qté", "qte"])
    uom_idx = _find_index(headers, ["unité", "unite", "uom", "um"])

    # Si pas d'en-tête reconnu, prendre la première colonne comme description
    if desc_idx is None:
        desc_idx = 0

    lines = []
    for row in table[1:]:
        if not row or len(row) <= desc_idx:
            continue
        desc = str(row[desc_idx]).strip() if row[desc_idx] else ""
        if not desc:
            continue

        qty = None
        if qty_idx is not None and len(row) > qty_idx and row[qty_idx]:
            try:
                qty = float(str(row[qty_idx]).replace(",", "."))
            except ValueError:
                pass

        uom = None
        if uom_idx is not None and len(row) > uom_idx and row[uom_idx]:
            uom = str(row[uom_idx]).strip()

        lines.append({"description": desc, "quantity": qty, "uom": uom})

    return lines


def _find_index(headers: list[str], candidates: list[str]) -> int | None:
    for i, h in enumerate(headers):
        for c in candidates:
            if c in h:
                return i
    return None
