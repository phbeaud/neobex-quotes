"""Gestion de la connexion SQLite et des sessions."""

from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from src.config import DB_URL
from src.db.models import Base

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)


def init_db():
    """Crée toutes les tables dans la base SQLite."""
    Base.metadata.create_all(engine)
    _run_migrations()
    return engine


def _run_migrations():
    """Ajoute les colonnes manquantes aux tables existantes."""
    inspector = inspect(engine)

    # Migration: ajouter client_price à quote_lines
    if "quote_lines" in inspector.get_table_names():
        columns = [c["name"] for c in inspector.get_columns("quote_lines")]
        if "client_price" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE quote_lines ADD COLUMN client_price FLOAT"))
                conn.commit()


def get_session():
    """Retourne une session DB."""
    return Session()


@contextmanager
def session_scope():
    """Context manager pour les sessions DB (évite les fuites)."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
