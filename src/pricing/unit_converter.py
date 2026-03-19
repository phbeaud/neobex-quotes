"""Conversion d'unités de mesure entre produit client et produit Neobex.

Détecte les différences de format (100 vs 1000 unités, 4L vs 10L, etc.)
et ajuste les prix pour une comparaison équitable.

Exemples:
- Couvre-chaussures: client a 100/pqt à 7.95$, Neobex a 1000/cs → conversion
- Sacs: client a 200/cs, Neobex a 150/cs → conversion
- Liquides: client a 4L, Neobex a 10L → conversion
"""
from __future__ import annotations

import re


def detect_unit_info(description: str) -> dict:
    """Extrait les informations d'unité d'une description produit.

    Returns:
        dict avec:
            - qty_per_unit: nombre d'items par unité d'achat (ex: 100, 500, 1000)
            - volume_liters: volume en litres si applicable
            - unit_type: 'count', 'volume', 'weight', 'length' ou 'unknown'
    """
    desc_lower = description.lower().strip()
    info = {
        "qty_per_unit": None,
        "volume_liters": None,
        "unit_type": "unknown",
        "raw_unit": None,
    }

    # ── Quantité par emballage ──
    # Patterns: (100/bte), (500/cs), (200/caisse), 48/case, 48 rouleaux, etc.
    qty_patterns = [
        r"(\d+)\s*/\s*(?:bte|boîte|boite|box|pqt|paquet|pack)",
        r"(\d+)\s*/\s*(?:cs|caisse|case|cse)",
        r"(\d+)\s*/\s*(?:rlx|rouleaux|rolls)",
        r"\((\d+)\s*/\s*\w+\)",                     # (100/bte), (500/cs)
        r"(\d+)\s*(?:un|unités|units)\s*/\s*\w+",
        r"(\d+)\s*rouleaux",
        r"(\d+)\s*feuilles",                         # 420 feuilles
    ]

    for pattern in qty_patterns:
        match = re.search(pattern, desc_lower)
        if match:
            qty = int(match.group(1))
            if qty > 1:
                info["qty_per_unit"] = qty
                info["unit_type"] = "count"
                info["raw_unit"] = match.group(0)
                break

    # ── Volume en litres ──
    # Patterns: 4L, 10L, 3.6L, 500ml, 946ml
    vol_patterns = [
        (r"(\d+(?:\.\d+)?)\s*(?:l|litres?|liters?)\b", 1.0),       # 4L, 10L, 3.6L
        (r"(\d+(?:\.\d+)?)\s*(?:ml|millilitres?)\b", 0.001),  # 500ml, 946ml
        (r"(\d+(?:,\d+)?)\s*(?:l|litres?)\b", 1.0),           # 3,6L (virgule)
    ]

    for pattern, multiplier in vol_patterns:
        match = re.search(pattern, desc_lower)
        if match:
            vol_str = match.group(1).replace(",", ".")
            volume = float(vol_str) * multiplier
            if volume > 0:
                info["volume_liters"] = volume
                if info["unit_type"] == "unknown":
                    info["unit_type"] = "volume"
                info["raw_unit"] = match.group(0)
                break

    return info


def calculate_unit_conversion(
    client_desc: str,
    neobex_desc: str,
    neobex_uom: str = None,
    client_price: float = None,
    neobex_price: float = None,
) -> dict:
    """Compare les unités entre un produit client et un produit Neobex.

    Returns:
        dict avec:
            - conversion_factor: ratio pour ajuster les prix (ex: 10.0 si Neobex a 10x plus)
            - adjusted_client_price: prix client ajusté pour comparaison unitaire
            - adjusted_neobex_price: prix Neobex ajusté pour comparaison unitaire
            - note: texte explicatif pour la soumission
            - has_conversion: True si une conversion a été appliquée
    """
    result = {
        "conversion_factor": 1.0,
        "adjusted_client_price": client_price,
        "adjusted_neobex_price": neobex_price,
        "note": None,
        "has_conversion": False,
    }

    # Combiner description Neobex + UOM pour plus d'info
    neobex_full = f"{neobex_desc} {neobex_uom or ''}"

    client_info = detect_unit_info(client_desc)
    neobex_info = detect_unit_info(neobex_full)

    # ── Conversion par quantité (100 vs 1000, 200 vs 150, etc.) ──
    if client_info["qty_per_unit"] and neobex_info["qty_per_unit"]:
        c_qty = client_info["qty_per_unit"]
        n_qty = neobex_info["qty_per_unit"]

        if c_qty != n_qty:
            factor = n_qty / c_qty
            result["conversion_factor"] = factor
            result["has_conversion"] = True

            if client_price is not None:
                # Prix client ajusté pour la même quantité que Neobex
                result["adjusted_client_price"] = round(client_price * factor, 2)

            result["note"] = (
                f"Format client: {c_qty} unités — Notre format: {n_qty} unités "
                f"(ratio {factor:.1f}x)"
            )

            if client_price is not None:
                result["note"] += (
                    f"\nPrix client ajusté pour {n_qty} unités: "
                    f"{result['adjusted_client_price']:.2f}$"
                )

    # ── Conversion par volume (4L vs 10L, etc.) ──
    elif client_info["volume_liters"] and neobex_info["volume_liters"]:
        c_vol = client_info["volume_liters"]
        n_vol = neobex_info["volume_liters"]

        if abs(c_vol - n_vol) > 0.01:  # Pas le même volume
            factor = n_vol / c_vol
            result["conversion_factor"] = factor
            result["has_conversion"] = True

            if client_price is not None:
                result["adjusted_client_price"] = round(client_price * factor, 2)

            # Format lisible
            def _fmt_vol(v):
                if v >= 1:
                    return f"{v:.1f}L" if v != int(v) else f"{int(v)}L"
                return f"{int(v * 1000)}ml"

            result["note"] = (
                f"Format client: {_fmt_vol(c_vol)} — Notre format: {_fmt_vol(n_vol)} "
                f"(ratio {factor:.1f}x)"
            )

            if client_price is not None:
                result["note"] += (
                    f"\nPrix client ajusté pour {_fmt_vol(n_vol)}: "
                    f"{result['adjusted_client_price']:.2f}$"
                )

    return result
