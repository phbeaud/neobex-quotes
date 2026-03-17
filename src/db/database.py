"""Gestion de la connexion SQLite et des sessions."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import DB_URL
from src.db.models import Base

engine = create_engine(DB_URL, echo=False)
Session = sessionmaker(bind=engine)


def init_db():
    """Crée toutes les tables dans la base SQLite."""
    Base.metadata.create_all(engine)
    return engine


def get_session():
    """Retourne une session DB."""
    return Session()
