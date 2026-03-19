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
    customer: str = typer.Option(None, help="Nom du client (recherche fuzzy dans Zoho)"),
    customer_id: str = typer.Option(None, help="ID client Zoho directement"),
    create_customer: bool = typer.Option(False, "--create", help="Créer le client s'il n'existe pas"),
):
    """Créer une soumission dans Zoho Invoice depuis une demande finalisée."""
    from src.zoho.estimates import push_finalized_quote
    from src.zoho.contacts import find_or_create_contact, search_contacts

    if not customer_id:
        if not customer:
            typer.echo("Spécifiez --customer 'Nom du client'")
            raise typer.Exit(1)

        result = find_or_create_contact(customer, auto_create=create_customer)

        if result["contact_id"]:
            customer_id = result["contact_id"]
            customer_name = result["contact_name"]
            if result.get("created"):
                typer.echo(f"✨ Nouveau client créé: {customer_name}")
            else:
                typer.echo(f"✅ Client trouvé: {customer_name} (score: {result['score']}%)")
        else:
            # Pas de match assez bon, montrer les suggestions
            typer.echo(f"❌ Aucun client exact pour '{customer}'.")
            suggestions = result.get("suggestions", [])
            if suggestions:
                typer.echo("\nSuggestions:")
                for i, s in enumerate(suggestions, 1):
                    typer.echo(f"  {i}. {s['contact_name']} ({s['score']}%)")
                typer.echo(f"\nPour utiliser un de ces clients: --customer-id <ID>")
            typer.echo(f"Pour créer un nouveau client: ajoutez --create")
            raise typer.Exit(1)
    else:
        customer_name = customer

    estimate = push_finalized_quote(request_id, customer_id, customer_name=customer_name)
    typer.echo(f"\n✅ Soumission créée dans Zoho: #{estimate.get('estimate_number', 'N/A')}")
    typer.echo(f"   ID: {estimate.get('estimate_id', 'N/A')}")

    # Résumé pricing
    summary = estimate.get("_pricing_summary", {})
    if summary:
        typer.echo(f"\n{'─' * 50}")
        typer.echo(f"📊 RÉSUMÉ DE LA SOUMISSION")
        typer.echo(f"   Produits inclus : {summary.get('items_included', 0)}")
        if summary.get("items_skipped", 0) > 0:
            typer.echo(f"   ⚠️  Produits exclus (marge < 5%) : {summary['items_skipped']}")
            for s in summary.get("skipped_details", []):
                typer.echo(f"      → {s['description'][:40]} (marge: {s['margin_pct']:.1f}%)")
        typer.echo(f"   Total soumission Neobex : {summary.get('total_neobex', 0):.2f}$")
        if "economie_pct" in summary:
            typer.echo(f"\n💰 ÉCONOMIES POUR LE CLIENT")
            typer.echo(f"   Le client paie actuellement : {summary['total_client_actuel']:.2f}$")
            typer.echo(f"   Notre soumission : {summary['total_neobex']:.2f}$")
            typer.echo(f"   Économie totale : {summary['economie_totale']:.2f}$ ({summary['economie_pct']:.1f}%)")
        typer.echo(f"{'─' * 50}")


@app.command()
def search_customer(
    name: str = typer.Argument(..., help="Nom ou partie du nom du client"),
):
    """Rechercher un client dans Zoho Invoice."""
    from src.zoho.contacts import search_contacts

    typer.echo(f"Recherche: '{name}'...")
    results = search_contacts(name)
    if not results:
        typer.echo("Aucun résultat.")
        return

    typer.echo(f"\n{'#':>3} | {'Score':>5} | {'Nom':40s} | {'Email'}")
    typer.echo("-" * 80)
    for i, r in enumerate(results, 1):
        typer.echo(f"{i:>3} | {r['score']:>4.0f}% | {r['contact_name']:40s} | {r.get('email', '')}")


@app.command()
def create_customer(
    name: str = typer.Argument(..., help="Nom du client à créer"),
    email: str = typer.Option(None, help="Email du client"),
    phone: str = typer.Option(None, help="Téléphone du client"),
):
    """Créer un nouveau client dans Zoho Invoice."""
    from src.zoho.contacts import create_contact

    contact = create_contact(name, email=email, phone=phone)
    typer.echo(f"✨ Client créé: {contact['contact_name']}")
    typer.echo(f"   ID: {contact['contact_id']}")


@app.command()
def dashboard():
    """Lancer le tableau de bord Streamlit."""
    import subprocess
    import sys
    typer.echo("Lancement du dashboard Neobex Quotes...")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "src/dashboard/app.py",
        "--server.port", "8501",
    ])
