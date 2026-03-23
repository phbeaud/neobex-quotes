"""Gestion de la connexion DB et des sessions.

L'engine et la session sont créés de façon lazy pour permettre
à Streamlit Cloud de charger les secrets avant la connexion.
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# Base importé de façon lazy pour éviter les imports circulaires sur Streamlit Cloud

_engine = None
_Session = None


def _get_engine():
    """Retourne l'engine DB (lazy singleton).

    Lit os.environ directement (pas config.DB_URL) pour éviter
    le problème de cache module Python sur Streamlit Cloud.
    """
    global _engine
    if _engine is None:
        import os
        supabase_url = os.environ.get("SUPABASE_URL", "")
        if supabase_url:
            db_url = supabase_url
        else:
            from pathlib import Path
            db_path = Path(__file__).resolve().parent.parent.parent / "neobex.db"
            db_url = f"sqlite:///{db_path}"
        _engine = create_engine(db_url, echo=False)
    # TOUJOURS vérifier que l'engine est bien PostgreSQL, sinon le recréer
    if "sqlite" in str(_engine.url):
        import os
        supabase_url = os.environ.get("SUPABASE_URL", "")
        if supabase_url:
            _engine = create_engine(supabase_url, echo=False)
    return _engine


def reset_engine():
    """Force la recréation de l'engine (utile si env vars changent)."""
    global _engine, _Session
    _engine = None
    _Session = None


def _get_session_factory():
    """Retourne la session factory (lazy singleton)."""
    global _Session
    if _Session is None:
        _Session = sessionmaker(bind=_get_engine())
    return _Session


# Propriétés pour compatibilité avec l'ancien code
@property
def engine():
    return _get_engine()


# Exposer engine et Session comme attributs du module
def __getattr__(name):
    if name == "engine":
        return _get_engine()
    if name == "Session":
        return _get_session_factory()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def init_db():
    """Crée toutes les tables dans la base."""
    from src.db.models import Base
    eng = _get_engine()
    Base.metadata.create_all(eng)
    _run_migrations()
    return eng


def _run_migrations():
    """Ajoute les colonnes manquantes aux tables existantes."""
    eng = _get_engine()
    inspector = inspect(eng)

    # Migration: ajouter client_price à quote_lines
    if "quote_lines" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("quote_lines")]
        if "client_price" not in columns:
            with eng.connect() as conn:
                conn.execute(text("ALTER TABLE quote_lines ADD COLUMN client_price FLOAT"))
                conn.commit()


def get_session():
    """Retourne une session DB."""
    return _get_session_factory()()


@contextmanager
def session_scope():
    """Context manager pour les sessions DB (évite les fuites)."""
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
