"""Point d'entrée principal du pipeline d'analyse."""

from pathlib import Path

from src.db.database import get_session
from src.db import repository as repo


def detect_file_type(filepath: str) -> str:
    """Détecte le type de fichier d'entrée."""
    ext = Path(filepath).suffix.lower()
    type_map = {
        ".xlsx": "excel",
        ".xls": "excel",
        ".csv": "csv",
        ".pdf": "pdf",
        ".txt": "text",
    }
    return type_map.get(ext, "text")


def run_analysis(filepath: str) -> int:
    """Pipeline complet d'analyse d'une demande client.

    1. Lire le fichier
    2. Extraire les lignes produits
    3. Normaliser
    4. Détecter les catégories
    5. Matcher
    6. Sauvegarder en DB

    Retourne l'ID de la demande créée.
    """
    from src.ingestion.excel_reader import read_client_file
    from src.ingestion.text_reader import read_text_file
    from src.ingestion.pdf_reader import read_pdf_file
    from src.normalization.cleaner import normalize_line
    from src.normalization.categories import detect_category
    from src.matching.engine import find_matches
    from src.config import MAX_SUGGESTIONS, AUTO_APPROVE_THRESHOLD, LOW_MATCH_THRESHOLD

    file_type = detect_file_type(filepath)

    # Étape 1-2: Lecture et extraction
    if file_type in ("excel", "csv"):
        lines = read_client_file(filepath)
    elif file_type == "pdf":
        lines = read_pdf_file(filepath)
    else:
        lines = read_text_file(filepath)

    session = get_session()
    try:
        # Créer la demande
        request = repo.create_quote_request(session, filepath, file_type)

        products = repo.get_all_products(session)

        for raw_line in lines:
            desc = raw_line.get("description", "")
            qty = raw_line.get("quantity")
            uom = raw_line.get("uom")

            # Étape 3: Normaliser
            norm_desc = normalize_line(desc)

            # Étape 4: Catégorie
            category = detect_category(norm_desc)

            # Créer la ligne
            quote_line = repo.add_quote_line(session, request.id, desc, qty, uom)
            quote_line.normalized_description = norm_desc
            quote_line.detected_category = category

            # Étape 5-6: Matching
            matches = find_matches(session, norm_desc, category, products)

            if not matches:
                quote_line.status = "not_found"
            else:
                best_score = matches[0]["score"]
                if best_score >= AUTO_APPROVE_THRESHOLD:
                    quote_line.status = "auto_approved"
                elif best_score >= LOW_MATCH_THRESHOLD:
                    quote_line.status = "to_review"
                else:
                    quote_line.status = "low_match"

                for rank, match in enumerate(matches[:MAX_SUGGESTIONS], 1):
                    repo.add_suggestion(
                        session,
                        quote_line.id,
                        match["product_id"],
                        rank,
                        match["score"],
                        match["reason"],
                    )

        session.commit()
        return request.id

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    from src.cli import app
    app()
