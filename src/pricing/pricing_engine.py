"""Moteur de pricing — placeholder pour Phase 2."""
from __future__ import annotations


def get_price(product_id: int) -> float | None:
    """Retourne le prix d'un produit. Pour l'instant, lit simplement le prix en DB."""
    from src.db.database import get_session
    from src.db.models import Product

    session = get_session()
    try:
        product = session.query(Product).get(product_id)
        return product.price if product else None
    finally:
        session.close()
