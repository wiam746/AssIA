"""Dependances FastAPI reutilisables (session DB, utilisateur courant, services)."""

from typing import Annotated, Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from api.auth import get_current_user
from models.database import User, get_db
from services.document_service import DocumentService
from services.email_service import EmailService
from services.incident_service import IncidentService
from services.projet_service import ProjetService
from services.reunion_service import ReunionService

# ----------------------------------------------------------------------
# Alias de types pour l'injection de dependances FastAPI
# ----------------------------------------------------------------------

DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_document_service(db: DbSession) -> DocumentService:
    return DocumentService(db=db)


def get_reunion_service(db: DbSession) -> ReunionService:
    return ReunionService(db=db)


def get_incident_service(db: DbSession) -> IncidentService:
    return IncidentService(db=db)


def get_projet_service(db: DbSession) -> ProjetService:
    return ProjetService(db=db)


def get_email_service(db: DbSession) -> EmailService:
    return EmailService(db=db)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
ReunionServiceDep = Annotated[ReunionService, Depends(get_reunion_service)]
IncidentServiceDep = Annotated[IncidentService, Depends(get_incident_service)]
ProjetServiceDep = Annotated[ProjetService, Depends(get_projet_service)]
EmailServiceDep = Annotated[EmailService, Depends(get_email_service)]
