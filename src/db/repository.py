"""Fonctions d'accès aux données (CRUD simple)."""
from __future__ import annotations

from sqlalchemy.orm import Session
from src.db.models import Product, QuoteRequest, QuoteLine, QuoteSuggestion, Equivalence


def get_all_products(session: Session, active_only: bool = True) -> list[Product]:
    query = session.query(Product)
    if active_only:
        query = query.filter(Product.is_active == True)
    return query.all()


def get_products_by_category(session: Session, category: str) -> list[Product]:
    return session.query(Product).filter(
        Product.category == category,
        Product.is_active == True,
    ).all()


def find_product_by_sku(session: Session, sku: str) -> Product | None:
    return session.query(Product).filter(Product.internal_sku == sku).first()


def create_quote_request(session: Session, source_file: str, source_type: str) -> QuoteRequest:
    qr = QuoteRequest(source_file=source_file, source_type=source_type)
    session.add(qr)
    session.flush()
    return qr


def add_quote_line(session: Session, request_id: int, raw_desc: str,
                   quantity: float = None, uom: str = None) -> QuoteLine:
    line = QuoteLine(
        quote_request_id=request_id,
        raw_description=raw_desc,
        quantity=quantity,
        uom=uom,
    )
    session.add(line)
    session.flush()
    return line


def add_suggestion(session: Session, line_id: int, product_id: int,
                   rank: int, score: float, reason: str) -> QuoteSuggestion:
    sugg = QuoteSuggestion(
        quote_line_id=line_id,
        product_id=product_id,
        rank=rank,
        score=score,
        reason=reason,
    )
    session.add(sugg)
    session.flush()
    return sugg


def get_known_equivalence(session: Session, description: str) -> Equivalence | None:
    """Cherche une équivalence déjà validée pour cette description.

    1. Match exact
    2. Match fuzzy (>= 95%) sur les descriptions d'équivalences
    """
    # Match exact
    exact = session.query(Equivalence).filter(
        Equivalence.source_description == description,
        Equivalence.validated_at.isnot(None),
    ).first()
    if exact:
        return exact

    # Match fuzzy sur les équivalences validées
    from rapidfuzz import fuzz
    all_equivs = session.query(Equivalence).filter(
        Equivalence.validated_at.isnot(None),
    ).all()

    best_match = None
    best_score = 0
    for eq in all_equivs:
        score = fuzz.token_sort_ratio(description, eq.source_description)
        if score > best_score and score >= 95:
            best_score = score
            best_match = eq

    return best_match
