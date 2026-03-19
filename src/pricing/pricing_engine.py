"""Moteur de pricing Neobex.

Stratégie de prix:
1. Prix fixes pour certains produits (gants vinyle = 3.99$, AdvanCare nitrile = 4.99$)
2. Si prix client disponible ET cost+33% >= prix client → prix = prix client - 5%
3. Sinon → cost + 33% de marge
"""
from __future__ import annotations

# ── Prix fixes par SKU ──────────────────────────────────────
FIXED_PRICES: dict[str, float] = {
    # Gants vinyle synthétique
    "VGPF3001": 3.99,
    # Gants nitrile AdvanCare
    "ANBM10014": 4.99,
}

# ── Marge par défaut ────────────────────────────────────────
DEFAULT_MARGIN = 0.33       # 33%
UNDERCUT_PERCENT = 0.05     # 5% en-dessous du prix client
MIN_MARGIN = 0.05           # 5% marge minimum — en dessous, on exclut le produit


def calculate_selling_price(
    product_cost: float | None,
    client_price: float | None,
    product_sku: str | None = None,
) -> dict:
    """Calcule le prix de vente optimal.

    Args:
        product_cost: Coût d'achat du produit (cost dans Zoho)
        client_price: Prix actuel que le client paie (None si inconnu)
        product_sku: SKU du produit (pour vérifier les prix fixes)

    Returns:
        dict avec:
            - selling_price: prix de vente calculé
            - strategy: explication de la stratégie utilisée
            - margin_pct: % de marge réel
            - savings_pct: % d'économie pour le client (None si pas de prix client)
    """
    result = {
        "selling_price": 0.0,
        "strategy": "",
        "margin_pct": 0.0,
        "savings_pct": None,
    }

    # 1. Prix fixe ?
    sku_upper = (product_sku or "").upper()
    for fixed_sku, fixed_price in FIXED_PRICES.items():
        if fixed_sku.upper() == sku_upper:
            result["selling_price"] = fixed_price
            result["strategy"] = f"prix_fixe ({fixed_sku})"
            if product_cost and product_cost > 0:
                result["margin_pct"] = ((fixed_price - product_cost) / product_cost) * 100
            if client_price and client_price > 0:
                result["savings_pct"] = ((client_price - fixed_price) / client_price) * 100
            return result

    # 2. Calcul standard
    if not product_cost or product_cost <= 0:
        # Pas de coût connu — on ne peut pas calculer
        result["selling_price"] = client_price or 0.0
        result["strategy"] = "prix_client_repris (pas de coût)"
        return result

    price_with_margin = round(product_cost * (1 + DEFAULT_MARGIN), 2)

    if client_price and client_price > 0:
        # On a le prix client
        if price_with_margin >= client_price:
            # Notre prix standard est plus cher → se positionner 5% sous le client
            undercut_price = round(client_price * (1 - UNDERCUT_PERCENT), 2)
            # Vérifier qu'on reste au-dessus du coût (pas vendre à perte)
            if undercut_price <= product_cost:
                # On ne peut pas être compétitif sans perdre de l'argent
                # On met le prix coûtant + 5% minimum
                undercut_price = round(product_cost * 1.05, 2)
                result["strategy"] = "marge_minimale (5%) — compétiteur très bas"
            else:
                result["strategy"] = f"undercut_client (-5% du prix client {client_price:.2f}$)"

            result["selling_price"] = undercut_price
            result["margin_pct"] = ((undercut_price - product_cost) / product_cost) * 100
            result["savings_pct"] = ((client_price - undercut_price) / client_price) * 100
        else:
            # Notre prix standard est déjà moins cher → utiliser cost+33%
            result["selling_price"] = price_with_margin
            result["strategy"] = f"marge_standard (33%)"
            result["margin_pct"] = DEFAULT_MARGIN * 100
            result["savings_pct"] = ((client_price - price_with_margin) / client_price) * 100
    else:
        # Pas de prix client → marge standard
        result["selling_price"] = price_with_margin
        result["strategy"] = "marge_standard (33%) — pas de prix client"
        result["margin_pct"] = DEFAULT_MARGIN * 100

    return result


def get_price(product_id: int) -> float | None:
    """Retourne le prix d'un produit (legacy, pour compatibilité)."""
    from src.db.database import get_session
    from src.db.models import Product

    session = get_session()
    try:
        product = session.query(Product).get(product_id)
        return product.price if product else None
    finally:
        session.close()
