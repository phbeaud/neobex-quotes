"""Modèles SQLAlchemy pour la base locale Neobex."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    internal_sku = Column(String(50), unique=True, nullable=True)
    source_name = Column(String(100))  # "zoho", "fournisseur_x", "import_prive"
    source_sku = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    category = Column(String(50))  # "epi", "papier", "chimique", "sacs", "autre"
    sub_category = Column(String(100), nullable=True)
    title = Column(String(255))
    description = Column(Text, nullable=True)
    normalized_description = Column(Text, nullable=True)
    uom = Column(String(20), nullable=True)  # unité de mesure
    case_qty = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    keywords = Column(Text, nullable=True)  # mots-clés séparés par virgules
    synonyms = Column(Text, nullable=True)  # synonymes séparés par virgules
    is_active = Column(Boolean, default=True)

    suggestions = relationship("QuoteSuggestion", back_populates="product")


class Equivalence(Base):
    __tablename__ = "equivalences"

    id = Column(Integer, primary_key=True)
    source_type = Column(String(50))  # "client", "fournisseur", "interne"
    source_name = Column(String(100))
    source_sku = Column(String(100), nullable=True)
    source_description = Column(Text)
    matched_product_id = Column(Integer, ForeignKey("products.id"))
    confidence_score = Column(Float)
    validated_by = Column(String(100), nullable=True)
    validated_at = Column(DateTime, nullable=True)

    product = relationship("Product")


class QuoteRequest(Base):
    __tablename__ = "quote_requests"

    id = Column(Integer, primary_key=True)
    source_file = Column(String(255), nullable=True)
    source_type = Column(String(50))  # "excel", "csv", "pdf", "text"
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(50), default="pending")  # pending, analyzed, reviewed, finalized

    lines = relationship("QuoteLine", back_populates="request")


class QuoteLine(Base):
    __tablename__ = "quote_lines"

    id = Column(Integer, primary_key=True)
    quote_request_id = Column(Integer, ForeignKey("quote_requests.id"))
    raw_description = Column(Text)
    normalized_description = Column(Text, nullable=True)
    quantity = Column(Float, nullable=True)
    uom = Column(String(20), nullable=True)
    detected_category = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")  # pending, auto_approved, to_review, not_found

    request = relationship("QuoteRequest", back_populates="lines")
    suggestions = relationship("QuoteSuggestion", back_populates="line")


class QuoteSuggestion(Base):
    __tablename__ = "quote_suggestions"

    id = Column(Integer, primary_key=True)
    quote_line_id = Column(Integer, ForeignKey("quote_lines.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    rank = Column(Integer)  # 1, 2, 3
    score = Column(Float)
    reason = Column(String(255))  # "exact_sku", "fuzzy_description", "synonym", etc.
    is_selected = Column(Boolean, default=False)

    line = relationship("QuoteLine", back_populates="suggestions")
    product = relationship("Product", back_populates="suggestions")


class ValidationHistory(Base):
    __tablename__ = "validation_history"

    id = Column(Integer, primary_key=True)
    quote_line_id = Column(Integer, ForeignKey("quote_lines.id"))
    selected_product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    previous_status = Column(String(50))
    new_status = Column(String(50))
    comment = Column(Text, nullable=True)
    validated_at = Column(DateTime, default=datetime.now)
