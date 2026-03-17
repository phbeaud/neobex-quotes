"""Tests pour la normalisation des descriptions."""

from src.normalization.cleaner import normalize_line
from src.normalization.categories import detect_category
from src.normalization.parser import extract_attributes
from src.normalization.attributes import check_critical_match


def test_normalize_sizes():
    assert "XL" in normalize_line("gants nitrile xl")
    assert "S" in normalize_line("gants petit")
    assert "M" in normalize_line("medium")


def test_normalize_colors():
    result = normalize_line("gants nitrile blk")
    assert "noir" in result


def test_normalize_case_format():
    result = normalize_line("papier 12/cs")
    assert "12/caisse" in result


def test_detect_category_epi():
    assert detect_category("gants nitrile bleu L") == "epi"


def test_detect_category_papier():
    assert detect_category("essuie-mains pli simple") == "papier"


def test_detect_category_chimique():
    assert detect_category("désinfectant surfaces") == "chimique"


def test_detect_category_sacs():
    assert detect_category("sacs poubelle 26x36") == "sacs"


def test_detect_category_unknown():
    assert detect_category("widget xyz inconnu") == "autre"


def test_extract_attributes_gants():
    attrs = extract_attributes("gants nitrile bleu L")
    assert attrs.get("material") == "nitrile"
    assert attrs.get("color") == "bleu"
    assert attrs.get("size") == "L"


def test_critical_match_blocks_size():
    source = {"size": "L", "material": "nitrile"}
    target = {"size": "M", "material": "nitrile"}
    assert check_critical_match("epi", source, target) is False


def test_critical_match_allows_same():
    source = {"size": "L", "material": "nitrile"}
    target = {"size": "L", "material": "nitrile"}
    assert check_critical_match("epi", source, target) is True


def test_critical_match_allows_missing():
    source = {"size": "L"}
    target = {}  # pas d'attribut taille détecté
    assert check_critical_match("epi", source, target) is True
