"""Lecture de texte brut (courriel, fichier .txt)."""
from __future__ import annotations

import re


def read_text_file(filepath: str) -> list[dict]:
    """Lit un fichier texte et extrait les lignes produits."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return parse_text(text)


def parse_text(text: str) -> list[dict]:
    """Parse du texte brut pour en extraire des lignes produits.

    Détecte les patterns courants:
    - lignes avec quantité en début (ex: "12 Gants nitrile L")
    - lignes avec quantité après tiret ou virgule
    - lignes simples (une description par ligne)
    """
    lines = []
    for raw in text.strip().splitlines():
        raw = raw.strip()
        if not raw or len(raw) < 3:
            continue
        # Ignorer les lignes qui ressemblent à des en-têtes ou signatures
        if _is_noise(raw):
            continue

        parsed = _parse_line(raw)
        if parsed:
            lines.append(parsed)

    return lines


def _parse_line(line: str) -> dict | None:
    """Essaie d'extraire description, quantité et unité d'une ligne."""
    # Pattern: "12 Gants nitrile L" ou "12x Gants nitrile"
    match = re.match(r"^(\d+)\s*[xX]?\s+(.+)$", line)
    if match:
        return {
            "description": match.group(2).strip(),
            "quantity": float(match.group(1)),
            "uom": None,
        }

    # Pattern: "Gants nitrile L - 12" ou "Gants nitrile, qty: 12"
    match = re.match(r"^(.+?)[\s,\-]+(?:qty|qté|quantité|x)?\s*:?\s*(\d+)\s*$", line, re.IGNORECASE)
    if match:
        return {
            "description": match.group(1).strip(),
            "quantity": float(match.group(2)),
            "uom": None,
        }

    # Ligne simple sans quantité
    return {
        "description": line,
        "quantity": None,
        "uom": None,
    }


def _is_noise(line: str) -> bool:
    """Détecte les lignes non pertinentes."""
    noise_patterns = [
        r"^(bonjour|salut|hello|hi|merci|cordialement|regards)",
        r"^(envoyé|sent|de:|from:|objet:|subject:)",
        r"^[-=_]{3,}$",
        r"^tel:|^fax:|^email:",
    ]
    lower = line.lower()
    return any(re.match(p, lower) for p in noise_patterns)
