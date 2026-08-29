"""
Connexion a la base de donnees SQLite via SQLAlchemy.

Definit les modeles ORM (tables) et expose une dependance FastAPI `get_db`
pour injecter une session de base de donnees dans les routes.
"""

import logging
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from config.settings import settings

logger = logging.getLogger("models.database")


class Base(DeclarativeBase):
    """Classe de base declarative pour tous les modeles ORM du projet."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# Moteur et session SQLAlchemy
# ----------------------------------------------------------------------

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=settings.app_debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependance FastAPI fournissant une session de base de donnees par requete."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Cree les tables en base si elles n'existent pas encore (appele au demarrage)."""
    logger.info("Initialisation de la base de donnees : %s", settings.database_url)
    Base.metadata.create_all(bind=engine)


# ----------------------------------------------------------------------
# Modeles ORM
# ----------------------------------------------------------------------


class User(Base):
    """Utilisateur de l'application, synchronise depuis Keycloak."""

    __tablename__ = "users"

    id = Column(String, primary_key=True)  # correspond au "sub" du token Keycloak
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class Document(Base):
    """Document uploade par un utilisateur (source de connaissance pour le RAG)."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    content_type = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending | processing | indexed | error
    error_message = Column(Text, nullable=True)
    uploaded_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    indexed_at = Column(DateTime, nullable=True)


class Conversation(Base):
    """Une conversation de chat entre un utilisateur et l'assistant."""

    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    projet_id = Column(String, ForeignKey("projets.id"), nullable=True)  # None = conversation globale
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=True)  # None = conversation globale ou projet
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)  # None = conversation globale/projet/incident
    title = Column(String, default="Nouvelle conversation")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Un message individuel au sein d'une conversation."""

    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant | system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Reunion(Base):
    """Compte-rendu de reunion traite par l'assistant."""

    __tablename__ = "reunions"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    meeting_date = Column(DateTime, nullable=True)
    participants = Column(Text, nullable=True)  # liste separee par virgules
    objet = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    decisions = Column(Text, nullable=True)
    actions = Column(Text, nullable=True)
    prochaine_reunion = Column(Text, nullable=True)
    status = Column(String, default="brouillon")  # brouillon | valide
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    document = relationship("Document")


class IncidentDocument(Base):
    """Table de jointure entre un incident et ses documents."""

    __tablename__ = "incident_documents"

    id = Column(String, primary_key=True)
    incident_id = Column(String, ForeignKey("incidents.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    document = relationship("Document")


class Incident(Base):
    """Incident technique ou operationnel suivi par l'assistant."""

    __tablename__ = "incidents"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, default="mineur")  # mineur | majeur | critique
    status = Column(String, default="ouvert")  # ouvert | en_cours | resolu | ferme
    analysis = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    reported_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    resolved_at = Column(DateTime, nullable=True)

    document = relationship("Document", foreign_keys=[document_id])
    incident_documents = relationship("IncidentDocument", cascade="all, delete-orphan",
                                     foreign_keys="IncidentDocument.incident_id")


class ProjetDocument(Base):
    """Table de jointure entre un projet et ses documents (plusieurs documents par projet)."""

    __tablename__ = "projet_documents"

    id = Column(String, primary_key=True)
    projet_id = Column(String, ForeignKey("projets.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    document = relationship("Document")


class Projet(Base):
    """Projet suivi au sein de l'application."""

    __tablename__ = "projets"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="actif")  # actif | en_pause | termine | archive
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)  # document principal (legacy)
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    document = relationship("Document", foreign_keys=[document_id])
    projet_documents = relationship("ProjetDocument", cascade="all, delete-orphan",
                                   foreign_keys="ProjetDocument.projet_id")


class EmailDraft(Base):
    """Brouillon d'email genere ou analyse par l'assistant."""

    __tablename__ = "email_drafts"

    id = Column(String, primary_key=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    tone = Column(String, default="neutre")
    mode = Column(String, default="redaction")  # redaction | analyse
    created_by = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
