"""Tests pour le moteur de matching."""

from unittest.mock import MagicMock
from src.matching.exact_match import try_exact_match
from src.matching.fuzzy_match import try_fuzzy_match


def _make_product(id, title, sku=None, normalized=None, synonyms=None, category="epi"):
    p = MagicMock()
    p.id = id
    p.title = title
    p.internal_sku = sku
    p.normalized_description = normalized or title.lower()
    p.synonyms = synonyms
    p.category = category
    return p


def test_exact_sku_match():
    products = [_make_product(1, "Gants Nitrile L", sku="GNL-100")]
    results = try_exact_match("gnl-100", products)
    assert len(results) == 1
    assert results[0]["reason"] == "exact_sku"
    assert results[0]["score"] == 100.0


def test_exact_description_match():
    products = [_make_product(1, "Gants nitrile bleu L", normalized="gants nitrile bleu L")]
    results = try_exact_match("gants nitrile bleu l", products)
    assert len(results) == 1
    assert results[0]["reason"] == "exact_description"


def test_synonym_match():
    products = [_make_product(1, "Gants Nitrile L", synonyms="gant bleu large,gant nitrile grand")]
    results = try_exact_match("gant bleu large", products)
    assert len(results) == 1
    assert results[0]["reason"] == "synonym"


def test_no_match():
    products = [_make_product(1, "Papier essuie-mains", category="papier")]
    results = try_exact_match("gants nitrile", products)
    assert len(results) == 0


def test_fuzzy_match_finds_similar():
    products = [
        _make_product(1, "Gants nitrile bleu L", normalized="gants nitrile bleu L"),
        _make_product(2, "Papier essuie-mains", normalized="papier essuie-mains", category="papier"),
    ]
    results = try_fuzzy_match("gant nitrile bleu large", products, threshold=50)
    assert len(results) >= 1
    assert results[0]["product_id"] == 1
