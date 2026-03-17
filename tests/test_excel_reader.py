"""Tests pour la lecture Excel."""

import tempfile
import pandas as pd
from src.ingestion.excel_reader import read_client_file


def test_read_client_excel():
    """Test lecture d'un fichier Excel client simple."""
    df = pd.DataFrame({
        "Description": ["Gants nitrile L", "Papier essuie-mains", "Sacs poubelle 26x36"],
        "Quantité": [10, 5, 20],
    })

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        df.to_excel(f.name, index=False)
        lines = read_client_file(f.name)

    assert len(lines) == 3
    assert lines[0]["description"] == "Gants nitrile L"
    assert lines[0]["quantity"] == 10.0
    assert lines[1]["description"] == "Papier essuie-mains"


def test_read_client_csv():
    """Test lecture d'un fichier CSV client."""
    df = pd.DataFrame({
        "produit": ["Savon à mains", "Désinfectant"],
        "qty": [3, 6],
    })

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        df.to_csv(f.name, index=False)
        lines = read_client_file(f.name)

    assert len(lines) == 2
    assert lines[0]["description"] == "Savon à mains"
