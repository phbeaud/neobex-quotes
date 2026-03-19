"""Export du fichier final après validation humaine."""

from pathlib import Path
from datetime import datetime
import pandas as pd
from src.db.database import get_session
from src.db.models import (
    QuoteLine, QuoteSuggestion, Product, ValidationHistory, Equivalence,
)
from src.config import EXPORTS_DIR
from src.normalization.cleaner import normalize_line


def export_final(review_file: str, request_id: int, output_path: str = None) -> str:
    """Lit le fichier de revue validé et génère le fichier final de soumission.

    Le fichier de revue doit avoir la colonne 'produit_choisi' remplie :
      - "1", "2" ou "3" pour choisir une suggestion
      - Un titre de produit exact (recherche en BD)
      - Vide = ignorer la ligne (sauf auto_approved qui prend suggestion #1)
    """
    df = pd.read_excel(review_file)
    session = get_session()

    try:
        final_rows = []
        equivalences_created = 0

        for _, row in df.iterrows():
            line_id = int(row["line_id"])
            chosen_raw = str(row.get("produit_choisi", "")).strip()
            price = row.get("prix_proposé")
            client_price_raw = row.get("prix_client")
            comment = str(row.get("commentaire", "")).strip()

            line = session.get(QuoteLine, line_id)
            if not line:
                continue

            product = None

            # Résoudre le produit choisi
            if chosen_raw in ("1", "2", "3"):
                # Choix par numéro de suggestion
                rank = int(chosen_raw)
                sugg = session.query(QuoteSuggestion).filter(
                    QuoteSuggestion.quote_line_id == line_id,
                    QuoteSuggestion.rank == rank,
                ).first()
                if sugg:
                    product = session.get(Product, sugg.product_id)
            elif chosen_raw and chosen_raw.lower() not in ("", "nan"):
                # Choix par titre exact ou SKU
                product = session.query(Product).filter(
                    Product.title == chosen_raw
                ).first()
                if not product:
                    product = session.query(Product).filter(
                        Product.internal_sku == chosen_raw
                    ).first()
            else:
                # Vide — pour auto_approved, prendre suggestion #1
                if line.status == "auto_approved":
                    sugg = session.query(QuoteSuggestion).filter(
                        QuoteSuggestion.quote_line_id == line_id,
                        QuoteSuggestion.rank == 1,
                    ).first()
                    if sugg:
                        product = session.get(Product, sugg.product_id)

            product_title = product.title if product else ""
            product_sku = product.internal_sku if product else ""
            product_price = product.price if product else None

            final_rows.append({
                "description_client": line.raw_description,
                "quantité": line.quantity,
                "unité": line.uom or "",
                "produit_neobex": product_title,
                "sku": product_sku,
                "prix_unitaire": price if pd.notna(price) else (product_price or ""),
                "commentaire": comment if comment.lower() != "nan" else "",
            })

            # Sauvegarder le prix client en DB (qu'il vienne du fichier ou de la saisie manuelle)
            if pd.notna(client_price_raw) and str(client_price_raw).strip():
                try:
                    line.client_price = float(client_price_raw)
                except (ValueError, TypeError):
                    pass

            # Historique de validation
            if product:
                history = ValidationHistory(
                    quote_line_id=line_id,
                    selected_product_id=product.id,
                    previous_status=line.status,
                    new_status="finalized",
                    comment=comment if comment.lower() != "nan" else None,
                )
                session.add(history)
                line.status = "finalized"

                # Créer une équivalence pour apprentissage futur
                existing_equiv = session.query(Equivalence).filter(
                    Equivalence.source_description == line.raw_description,
                    Equivalence.matched_product_id == product.id,
                ).first()

                if not existing_equiv:
                    equiv = Equivalence(
                        source_type="client",
                        source_name="validation_manuelle",
                        source_description=line.raw_description,
                        matched_product_id=product.id,
                        confidence_score=100.0,
                        validated_by="humain",
                        validated_at=datetime.now(),
                    )
                    session.add(equiv)
                    equivalences_created += 1

        session.commit()

        df_final = pd.DataFrame(final_rows)

        if not output_path:
            EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(EXPORTS_DIR / f"soumission_{request_id}_{timestamp}.xlsx")

        df_final.to_excel(output_path, index=False, sheet_name="Soumission")

        print(f"  {equivalences_created} nouvelles équivalences apprises")
        return output_path

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
