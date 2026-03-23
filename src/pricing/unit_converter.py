"""Conversion d'unités pour comparaison de prix équitable."""
from __future__ import annotations
import re


def extract_unit_info(description: str, uom: str = None, case_qty: int = None) -> dict:
    """Extrait les informations d'unité d'un produit.

    Returns:
        dict with:
            - qty_per_unit: nombre d'items par unité vendue (100/bte, 500/cs, etc.)
            - volume_liters: volume en litres si applicable (4L, 10L, etc.)
            - unit_type: 'piece', 'volume', 'roll', 'sheet', etc.
    """
    text = f"{description} {uom or ''}".lower()
    result = {"qty_per_unit": 1, "volume_liters": None, "unit_type": "piece"}

    # Détecter quantité par unité: (100/bte), (500/cs), (200/cs), (48rlx), etc.
    qty_patterns = [
        r'(\d+)\s*/\s*(?:bte|boîte|boite|box|bx)',
        r'(\d+)\s*/\s*(?:cs|caisse|case)',
        r'(\d+)\s*/\s*(?:pqt|paquet|pkg)',
        r'(\d+)\s*(?:rlx|rouleaux|rolls)\s*/\s*(?:caisse|case|cs)',
        r'(\d+)\s*(?:rlx|rouleaux|rolls)',
        r'(\d+)\s*/\s*(?:sac|bag)',
    ]
    for pattern in qty_patterns:
        match = re.search(pattern, text)
        if match:
            result["qty_per_unit"] = int(match.group(1))
            break

    # Si case_qty est fourni et > qty détecté, utiliser case_qty
    if case_qty and case_qty > result["qty_per_unit"]:
        result["qty_per_unit"] = case_qty

    # Détecter volume en litres: 4L, 10L, 3.6L, 3,6L, 946ml, 500ml
    vol_match = re.search(r'(\d+(?:[.,]\d+)?)\s*[lL](?:\s|$|/)', text)
    if vol_match:
        result["volume_liters"] = float(vol_match.group(1).replace(',', '.'))
        result["unit_type"] = "volume"
    else:
        ml_match = re.search(r'(\d+)\s*ml', text)
        if ml_match:
            result["volume_liters"] = int(ml_match.group(1)) / 1000
            result["unit_type"] = "volume"

    # Détecter type de produit
    if any(w in text for w in ['rouleau', 'roll', 'rlx', 'papier hygiénique', 'essuie']):
        result["unit_type"] = "roll"
    elif any(w in text for w in ['feuille', 'sheet', 'lingette', 'wipe', 'serviette']):
        result["unit_type"] = "sheet"
    elif any(w in text for w in ['sac', 'bag', 'garbage']):
        result["unit_type"] = "bag"

    return result


def compare_units(
    client_desc: str, client_price: float, client_uom: str,
    neobex_desc: str, neobex_price: float, neobex_uom: str = None,
    neobex_case_qty: int = None,
) -> dict:
    """Compare les prix en normalisant les unités.

    Returns:
        dict with:
            - client_unit_price: prix par unité normalisée du client
            - neobex_unit_price: prix par unité normalisée de Neobex
            - conversion_note: explication de la conversion (pour affichage)
            - savings_pct: % d'économie réel après conversion
            - adjustment_factor: facteur multiplicateur pour ajuster la quantité
    """
    client_info = extract_unit_info(client_desc, client_uom)
    neobex_info = extract_unit_info(neobex_desc, neobex_uom, neobex_case_qty)

    result = {
        "client_unit_price": client_price,
        "neobex_unit_price": neobex_price,
        "conversion_note": None,
        "savings_pct": None,
        "adjustment_factor": 1.0,
    }

    # Comparaison par volume (litres)
    if client_info["volume_liters"] and neobex_info["volume_liters"]:
        client_per_liter = client_price / client_info["volume_liters"]
        neobex_per_liter = neobex_price / neobex_info["volume_liters"]

        result["client_unit_price"] = round(client_per_liter, 2)
        result["neobex_unit_price"] = round(neobex_per_liter, 2)
        result["conversion_note"] = (
            f"Client: {client_price:.2f}$/{client_info['volume_liters']}L = "
            f"{client_per_liter:.2f}$/L | "
            f"Neobex: {neobex_price:.2f}$/{neobex_info['volume_liters']}L = "
            f"{neobex_per_liter:.2f}$/L"
        )
        result["adjustment_factor"] = client_info["volume_liters"] / neobex_info["volume_liters"]
        if client_per_liter > 0:
            result["savings_pct"] = ((client_per_liter - neobex_per_liter) / client_per_liter) * 100
        return result

    # Comparaison par quantité (pièces)
    if client_info["qty_per_unit"] != neobex_info["qty_per_unit"]:
        client_per_piece = client_price / client_info["qty_per_unit"]
        neobex_per_piece = neobex_price / neobex_info["qty_per_unit"]

        result["client_unit_price"] = round(client_per_piece, 4)
        result["neobex_unit_price"] = round(neobex_per_piece, 4)
        result["conversion_note"] = (
            f"Client: {client_price:.2f}$/{client_info['qty_per_unit']} = "
            f"{client_per_piece:.4f}$/unité | "
            f"Neobex: {neobex_price:.2f}$/{neobex_info['qty_per_unit']} = "
            f"{neobex_per_piece:.4f}$/unité"
        )
        result["adjustment_factor"] = client_info["qty_per_unit"] / neobex_info["qty_per_unit"]
        if client_per_piece > 0:
            result["savings_pct"] = ((client_per_piece - neobex_per_piece) / client_per_piece) * 100
        return result

    # Même unité, comparaison directe
    if client_price > 0:
        result["savings_pct"] = ((client_price - neobex_price) / client_price) * 100
    return result
