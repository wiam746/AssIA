"""Service d'orchestration pour la création, le suivi des incidents, leurs documents et leurs discussions."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from agents.chat_agent import ChatAgent
from agents.incident_agent import IncidentAgent
from core.utils import generate_uuid, utcnow
from models.database import Conversation, Document, Incident, IncidentDocument, Message

logger = logging.getLogger("services.incident_service")


class IncidentService:
    """Orchestration entre l'agent d'analyse d'incidents, les documents, le chat et la persistance en base."""

    def __init__(
        self,
        db: Session,
        incident_agent: Optional[IncidentAgent] = None,
        chat_agent: Optional[ChatAgent] = None,
    ) -> None:
        self.db = db
        self.incident_agent = incident_agent or IncidentAgent()
        self.chat_agent = chat_agent or ChatAgent()

    async def create_incident(
        self,
        *,
        title: str,
        description: str,
        severity: str = "mineur",
        document_id: Optional[str] = None,
        reported_by: Optional[str] = None,
    ) -> Incident:
        """Cree un incident, l'analyse via l'agent, et persiste le resultat."""
        analysis = await self.incident_agent.analyze_incident(
            title=title,
            description=description,
            severity_hint=severity,
        )

        incident = Incident(
            id=generate_uuid(),
            title=title,
            description=description,
            severity=severity,
            status="ouvert",
            analysis=analysis,
            document_id=document_id,
            reported_by=reported_by,
        )
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        logger.info("Incident '%s' cree et analyse (id=%s).", title, incident.id)
        return incident

    def list_incidents(self, status: Optional[str] = None) -> List[Incident]:
        query = self.db.query(Incident)
        if status:
            query = query.filter(Incident.status == status)
        return query.order_by(Incident.created_at.desc()).all()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def update_incident(
        self,
        incident_id: str,
        *,
        status: Optional[str] = None,
        resolution: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Optional[Incident]:
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        if status:
            incident.status = status
            if status in {"resolu", "ferme"}:
                incident.resolved_at = utcnow()
            else:
                incident.resolved_at = None

        if resolution is not None:
            incident.resolution = resolution

        if document_id is not None:
            incident.document_id = document_id

        self.db.commit()
        self.db.refresh(incident)
        return incident

    def delete_incident(self, incident_id: str) -> bool:
        incident = self.get_incident(incident_id)
        if not incident:
            return False
        self.db.delete(incident)
        self.db.commit()
        return True

    # -----------------------------------------------------------------------
    # Documents de l'incident
    # -----------------------------------------------------------------------

    def list_incident_documents(self, incident_id: str) -> List[Document]:
        """Retourne tous les documents liés à cet incident."""
        links = (
            self.db.query(IncidentDocument)
            .filter(IncidentDocument.incident_id == incident_id)
            .all()
        )
        return [lnk.document for lnk in links if lnk.document]

    def add_document_to_incident(self, incident_id: str, document_id: str) -> Optional[IncidentDocument]:
        """Lie un document existant à un incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            return None

        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None

        existing = (
            self.db.query(IncidentDocument)
            .filter(
                IncidentDocument.incident_id == incident_id,
                IncidentDocument.document_id == document_id,
            )
            .first()
        )
        if existing:
            return existing

        link = IncidentDocument(
            id=generate_uuid(),
            incident_id=incident_id,
            document_id=document_id,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        logger.info("Document %s ajouté à l'incident %s.", document_id, incident_id)
        return link

    def remove_document_from_incident(self, incident_id: str, document_id: str) -> bool:
        """Détache un document d'un incident."""
        link = (
            self.db.query(IncidentDocument)
            .filter(
                IncidentDocument.incident_id == incident_id,
                IncidentDocument.document_id == document_id,
            )
            .first()
        )
        if not link:
            return False
        self.db.delete(link)
        self.db.commit()
        return True

    # -----------------------------------------------------------------------
    # Chat / Discussions de l'incident
    # -----------------------------------------------------------------------

    def _get_or_create_incident_conversation(
        self, incident_id: str, conversation_id: Optional[str], user_id: str
    ) -> Conversation:
        if conversation_id:
            conv = (
                self.db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                    Conversation.incident_id == incident_id,
                )
                .first()
            )
            if conv:
                return conv

        incident = self.get_incident(incident_id)
        title = f"Discussion — {incident.title}" if incident else "Discussion incident"
        conv = Conversation(
            id=generate_uuid(),
            user_id=user_id,
            incident_id=incident_id,
            title=title,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_incident_conversations(self, incident_id: str, user_id: str) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.incident_id == incident_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    async def chat_with_incident(
        self,
        *,
        incident_id: str,
        message: str,
        conversation_id: Optional[str],
        user_id: str,
        user_name: Optional[str] = None,
    ) -> dict:
        """Envoie un message dans la discussion de cet incident."""
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident introuvable : {incident_id}")

        conversation = self._get_or_create_incident_conversation(incident_id, conversation_id, user_id)

        user_msg = Message(
            id=generate_uuid(),
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.db.add(user_msg)
        self.db.commit()

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages
            if m.role in {"user", "assistant"}
        ]

        incident_context = (
            f"Tu assistes le traitement de l'incident : «{incident.title}».\n"
            f"Description : {incident.description}.\n"
            f"Sévérité : {incident.severity} | Statut : {incident.status}.\n"
            f"Analyse IA : {incident.analysis or 'Non effectuée'}.\n"
            f"Résolution : {incident.resolution or 'En cours'}.\n"
        )

        inc_docs = self.list_incident_documents(incident_id)
        doc_ids = [d.id for d in inc_docs]
        if incident.document_id and incident.document_id not in doc_ids:
            doc_ids.append(incident.document_id)

        answer = await self.chat_agent.answer(
            message,
            history=history,
            user_name=user_name,
            extra_context=incident_context,
            document_ids=doc_ids if doc_ids else None,
        )

        assistant_msg = Message(
            id=generate_uuid(),
            conversation_id=conversation.id,
            role="assistant",
            content=answer.content,
        )
        self.db.add(assistant_msg)
        conversation.updated_at = utcnow()
        self.db.commit()
        self.db.refresh(assistant_msg)

        return {
            "conversation_id": conversation.id,
            "message": {
                "id": assistant_msg.id,
                "role": assistant_msg.role,
                "content": assistant_msg.content,
                "created_at": assistant_msg.created_at.isoformat(),
            },
            "sources": answer.sources,
        }
