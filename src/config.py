"""Configuration centrale du projet Neobex Quotes."""

from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Chemins projet
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CATALOGS_DIR = DATA_DIR / "catalogs"
EXPORTS_DIR = PROJECT_ROOT / "exports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Base de données
DB_PATH = PROJECT_ROOT / "neobex.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Matching
FUZZY_THRESHOLD = 55  # score minimum pour un match fuzzy
AUTO_APPROVE_THRESHOLD = 85  # score minimum pour auto-approuver
LOW_MATCH_THRESHOLD = 65  # en-dessous = "low_match" (match faible, à vérifier)
MAX_SUGGESTIONS = 3  # nombre max de suggestions par ligne

# Catégories connues
CATEGORIES = [
    "epi",
    "papier",
    "chimique",
    "sacs",
    "emballage",
    "entretien",
    "autre",
]

# Zoho Invoice (Phase 2) — TODO: configurer via .env
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID", "")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET", "")
ZOHO_ORG_ID = os.getenv("ZOHO_ORG_ID", "")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "")
