"""Export du fichier Excel de revue pour validation humaine."""

from pathlib import Path
from datetime import datetime
import pandas as pd
from src.db.database import get_session
from src.db.models import QuoteRequest, QuoteLine, QuoteSuggestion, Product
from src.config import EXPORTS_DIR


def export_review(request_id: int, output_path: str = None) -> str:
    """Génère le fichier Excel de revue pour une demande donnée."""
    session = get_session()
    try:
        request = session.query(QuoteRequest).get(request_id)
        if not request:
            raise ValueError(f"Demande #{request_id} introuvable")

        lines = session.query(QuoteLine).filter(
            QuoteLine.quote_request_id == request_id
        ).all()

        rows = []
        for line in lines:
            suggestions = session.query(QuoteSuggestion).filter(
                QuoteSuggestion.quote_line_id == line.id
            ).order_by(QuoteSuggestion.rank).all()

            row = {
                "line_id": line.id,
                "description_client": line.raw_description,
                "quantité": line.quantity,
                "unité": line.uom or "",
                "catégorie_détectée": line.detected_category or "",
            }

            for i in range(3):
                prefix = f"suggestion_{i+1}"
                if i < len(suggestions):
                    s = suggestions[i]
                    product = session.query(Product).get(s.product_id)
                    row[prefix] = product.title if product else ""
                    row[f"score_{i+1}"] = s.score
                    row[f"sku_{i+1}"] = product.internal_sku or "" if product else ""
                else:
                    row[prefix] = ""
                    row[f"score_{i+1}"] = ""
                    row[f"sku_{i+1}"] = ""

            row["statut"] = line.status
            row["commentaire"] = ""
            # Pré-remplir pour les auto_approved avec suggestion #1
            if line.status == "auto_approved" and suggestions:
                row["produit_choisi"] = "1"
            else:
                row["produit_choisi"] = ""
            # Prix client : pré-rempli si détecté dans le fichier, sinon éditable
            row["prix_client"] = line.client_price if line.client_price else ""
            row["prix_proposé"] = ""

            rows.append(row)

        df = pd.DataFrame(rows)

        if not output_path:
            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(EXPORTS_DIR / f"revue_{request_id}_{timestamp}.xlsx")

        df.to_excel(output_path, index=False, sheet_name="Revue")
        return output_path

    finally:
        session.close()
