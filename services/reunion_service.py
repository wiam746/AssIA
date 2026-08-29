"""Service d'orchestration pour le traitement des comptes-rendus de reunion."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from agents.meeting_agent import MeetingAgent
from core.utils import generate_uuid
from models.database import Reunion

logger = logging.getLogger("services.reunion_service")


class ReunionService:
    """Orchestration entre l'agent de reunion et la persistance en base."""

    def __init__(self, db: Session, meeting_agent: Optional[MeetingAgent] = None) -> None:
        self.db = db
        self.meeting_agent = meeting_agent or MeetingAgent()

    async def create_reunion(
        self,
        *,
        title: str,
        raw_content: str,
        meeting_date=None,
        participants: Optional[str] = None,
        objet: Optional[str] = None,
        document_id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> Reunion:
        """Traite un compte-rendu brut via l'agent, puis persiste le resultat en statut 'brouillon'."""
        analysis = await self.meeting_agent.process_meeting(
            title=title,
            raw_content=raw_content,
            participants=participants,
        )

        reunion = Reunion(
            id=generate_uuid(),
            title=title,
            meeting_date=meeting_date,
            participants=participants,
            objet=objet or analysis.objet,
            raw_content=raw_content,
            summary=analysis.summary,
            decisions=analysis.decisions,
            actions=analysis.actions,
            prochaine_reunion=analysis.prochaine_reunion,
            status="brouillon",  # En attente de validation humaine
            document_id=document_id,
            created_by=created_by,
        )
        self.db.add(reunion)
        self.db.commit()
        self.db.refresh(reunion)

        logger.info("Réunion '%s' rédigée par l'IA et enregistrée en brouillon (id=%s).", title, reunion.id)
        return reunion

    def list_reunions(self, created_by: Optional[str] = None) -> List[Reunion]:
        query = self.db.query(Reunion)
        if created_by:
            query = query.filter(Reunion.created_by == created_by)
        return query.order_by(Reunion.created_at.desc()).all()

    def get_reunion(self, reunion_id: str) -> Optional[Reunion]:
        return self.db.query(Reunion).filter(Reunion.id == reunion_id).first()

    def update_reunion(
        self,
        reunion_id: str,
        *,
        title: Optional[str] = None,
        meeting_date=None,
        participants: Optional[str] = None,
        objet: Optional[str] = None,
        summary: Optional[str] = None,
        decisions: Optional[str] = None,
        actions: Optional[str] = None,
        prochaine_reunion: Optional[str] = None,
        status: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Optional[Reunion]:
        """Met à jour un procès-verbal et/ou le valide (Validation Humaine)."""
        reunion = self.get_reunion(reunion_id)
        if not reunion:
            return None

        if title is not None:
            reunion.title = title
        if meeting_date is not None:
            reunion.meeting_date = meeting_date
        if participants is not None:
            reunion.participants = participants
        if objet is not None:
            reunion.objet = objet
        if summary is not None:
            reunion.summary = summary
        if decisions is not None:
            reunion.decisions = decisions
        if actions is not None:
            reunion.actions = actions
        if prochaine_reunion is not None:
            reunion.prochaine_reunion = prochaine_reunion
        if status is not None:
            reunion.status = status
        if document_id is not None:
            reunion.document_id = document_id

        self.db.commit()
        self.db.refresh(reunion)
        logger.info("Réunion id=%s mise à jour (statut=%s).", reunion_id, reunion.status)
        return reunion

    def delete_reunion(self, reunion_id: str) -> bool:
        reunion = self.get_reunion(reunion_id)
        if not reunion:
            return False
        self.db.delete(reunion)
        self.db.commit()
        return True
