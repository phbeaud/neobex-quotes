"""Interface CLI Typer pour Neobex Quotes."""

from pathlib import Path
import typer

app = typer.Typer(help="Neobex Quotes — Outil de préparation de soumissions")


@app.command()
def init_db():
    """Initialiser la base SQLite."""
    from src.db.database import init_db as _init_db
    _init_db()
    typer.echo("Base de données initialisée avec succès.")


@app.command()
def import_products(
    file: Path = typer.Argument(..., help="Fichier Excel ou CSV du catalogue produits"),
):
    """Importer un catalogue produits depuis un Excel ou CSV."""
    from src.ingestion.excel_reader import import_catalog
    count = import_catalog(str(file))
    typer.echo(f"{count} produits importés.")


@app.command()
def analyze(
    file: Path = typer.Argument(..., help="Fichier client (Excel, CSV, PDF ou texte)"),
):
    """Analyser une demande client et générer les suggestions de matching."""
    from src.main import run_analysis
    request_id = run_analysis(str(file))
    typer.echo(f"Analyse terminée. Demande #{request_id} créée.")
    typer.echo("Utilisez 'review-export' pour exporter le fichier de revue.")


@app.command()
def review_export(
    request_id: int = typer.Argument(..., help="ID de la demande à exporter"),
    output: Path = typer.Option(None, help="Chemin du fichier Excel de sortie"),
):
    """Exporter le fichier Excel de revue pour validation humaine."""
    from src.outputs.export_review_excel import export_review
    out_path = export_review(request_id, str(output) if output else None)
    typer.echo(f"Fichier de revue exporté: {out_path}")


@app.command()
def finalize(
    file: Path = typer.Argument(..., help="Fichier Excel de revue validé"),
    request_id: int = typer.Argument(..., help="ID de la demande"),
):
    """Générer le fichier final après validation humaine."""
    from src.outputs.export_final_excel import export_final
    out_path = export_final(str(file), request_id)
    typer.echo(f"Fichier final exporté: {out_path}")


@app.command()
def sync_zoho_items():
    """Synchroniser les items depuis Zoho Invoice vers la base locale."""
    from src.zoho.items import sync_items
    count = sync_items()
    typer.echo(f"{count} produits synchronisés depuis Zoho Invoice.")


@app.command()
def push_zoho_estimate(
    request_id: int = typer.Argument(..., help="ID de la demande finalisée"),
    customer: str = typer.Option(None, help="Nom du client (recherche dans Zoho)"),
    customer_id: str = typer.Option(None, help="ID client Zoho directement"),
):
    """Créer une soumission dans Zoho Invoice depuis une demande finalisée."""
    from src.zoho.estimates import push_finalized_quote, get_contacts

    if not customer_id:
        if not customer:
            typer.echo("Spécifiez --customer ou --customer-id")
            raise typer.Exit(1)

        contacts = get_contacts(customer)
        if not contacts:
            typer.echo(f"Client '{customer}' introuvable dans Zoho.")
            raise typer.Exit(1)

        contact = contacts[0]
        customer_id = contact["contact_id"]
        customer_name = contact["contact_name"]
        typer.echo(f"Client trouvé: {customer_name} (ID: {customer_id})")
    else:
        customer_name = customer

    estimate = push_finalized_quote(request_id, customer_id, customer_name=customer_name)
    typer.echo(f"Soumission créée dans Zoho: #{estimate.get('estimate_number', 'N/A')}")
    typer.echo(f"ID: {estimate.get('estimate_id', 'N/A')}")
