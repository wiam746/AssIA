"""Service d'orchestration pour la redaction et l'analyse d'emails via l'agent email."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from agents.email_agent import EmailAgent
from core.utils import generate_uuid
from models.database import EmailDraft

logger = logging.getLogger("services.email_service")


class EmailService:
    """Orchestration entre l'agent email et la persistance des brouillons en base."""

    def __init__(self, db: Session, email_agent: Optional[EmailAgent] = None) -> None:
        self.db = db
        self.email_agent = email_agent or EmailAgent()

    async def draft_email(
        self,
        *,
        instructions: str,
        tone: str = "neutre",
        recipient_name: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> EmailDraft:
        """Genere un brouillon d'email a partir d'instructions, et le persiste."""
        subject, body = await self.email_agent.draft_email(
            instructions=instructions,
            tone=tone,
            recipient_name=recipient_name,
        )

        draft = EmailDraft(
            id=generate_uuid(),
            subject=subject,
            body=body,
            tone=tone,
            mode="redaction",
            created_by=created_by,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        logger.info("Brouillon d'email genere (id=%s).", draft.id)
        return draft

    async def analyze_email(
        self,
        *,
        email_content: str,
        created_by: Optional[str] = None,
    ) -> EmailDraft:
        """Analyse un email existant et persiste le resultat de l'analyse."""
        analysis = await self.email_agent.analyze_email(email_content=email_content)

        draft = EmailDraft(
            id=generate_uuid(),
            subject=None,
            body=analysis,
            tone="neutre",
            mode="analyse",
            created_by=created_by,
        )
        self.db.add(draft)
        self.db.commit()
        self.db.refresh(draft)

        return draft

    def list_drafts(self, created_by: Optional[str] = None) -> List[EmailDraft]:
        query = self.db.query(EmailDraft)
        if created_by:
            query = query.filter(EmailDraft.created_by == created_by)
        return query.order_by(EmailDraft.created_at.desc()).all()

    def get_draft(self, draft_id: str) -> Optional[EmailDraft]:
        return self.db.query(EmailDraft).filter(EmailDraft.id == draft_id).first()
