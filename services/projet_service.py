"""Service d'orchestration pour la gestion des projets (CRUD + documents + chat projet)."""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from agents.chat_agent import ChatAgent
from agents.project_agent import ProjectAgent
from core.utils import generate_uuid
from models.database import Conversation, Document, Message, Projet, ProjetDocument
from models.schemas import DocumentRead

logger = logging.getLogger("services.projet_service")


class ProjetService:
    """Orchestration entre l'agent projet et la persistance en base."""

    def __init__(
        self,
        db: Session,
        project_agent: Optional[ProjectAgent] = None,
        chat_agent: Optional[ChatAgent] = None,
    ) -> None:
        self.db = db
        self.project_agent = project_agent or ProjectAgent()
        self.chat_agent = chat_agent or ChatAgent()

    def create_projet(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        document_id: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> Projet:
        projet = Projet(
            id=generate_uuid(),
            name=name,
            description=description,
            status="actif",
            document_id=document_id,
            owner_id=owner_id,
        )
        self.db.add(projet)
        self.db.commit()
        self.db.refresh(projet)
        logger.info("Projet '%s' créé (id=%s).", name, projet.id)
        return projet

    def list_projets(self, owner_id: Optional[str] = None) -> List[Projet]:
        query = self.db.query(Projet)
        if owner_id:
            query = query.filter(Projet.owner_id == owner_id)
        return query.order_by(Projet.created_at.desc()).all()

    def get_projet(self, projet_id: str) -> Optional[Projet]:
        return self.db.query(Projet).filter(Projet.id == projet_id).first()

    def update_projet(
        self,
        projet_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> Optional[Projet]:
        projet = self.get_projet(projet_id)
        if not projet:
            return None

        if name:
            projet.name = name
        if description is not None:
            projet.description = description
        if status:
            projet.status = status
        if document_id is not None:
            projet.document_id = document_id

        self.db.commit()
        self.db.refresh(projet)
        return projet

    def delete_projet(self, projet_id: str) -> bool:
        projet = self.get_projet(projet_id)
        if not projet:
            return False
        self.db.delete(projet)
        self.db.commit()
        return True

    # -----------------------------------------------------------------------
    # Documents du projet
    # -----------------------------------------------------------------------

    def list_projet_documents(self, projet_id: str) -> List[Document]:
        """Retourne tous les documents liés à ce projet."""
        links = (
            self.db.query(ProjetDocument)
            .filter(ProjetDocument.projet_id == projet_id)
            .all()
        )
        return [lnk.document for lnk in links if lnk.document]

    def add_document_to_projet(self, projet_id: str, document_id: str) -> Optional[ProjetDocument]:
        """Lie un document existant à un projet (vérifie que document existe)."""
        projet = self.get_projet(projet_id)
        if not projet:
            return None

        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return None

        # Éviter les doublons
        existing = (
            self.db.query(ProjetDocument)
            .filter(
                ProjetDocument.projet_id == projet_id,
                ProjetDocument.document_id == document_id,
            )
            .first()
        )
        if existing:
            return existing

        link = ProjetDocument(
            id=generate_uuid(),
            projet_id=projet_id,
            document_id=document_id,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        logger.info("Document %s ajouté au projet %s.", document_id, projet_id)
        return link

    def remove_document_from_projet(self, projet_id: str, document_id: str) -> bool:
        """Détache un document d'un projet."""
        link = (
            self.db.query(ProjetDocument)
            .filter(
                ProjetDocument.projet_id == projet_id,
                ProjetDocument.document_id == document_id,
            )
            .first()
        )
        if not link:
            return False
        self.db.delete(link)
        self.db.commit()
        return True

    # -----------------------------------------------------------------------
    # Chat / Discussion contextuelle du projet
    # -----------------------------------------------------------------------

    def _get_or_create_project_conversation(
        self, projet_id: str, conversation_id: Optional[str], user_id: str
    ) -> Conversation:
        """Récupère ou crée une conversation associée à ce projet."""
        if conversation_id:
            conv = (
                self.db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                    Conversation.projet_id == projet_id,
                )
                .first()
            )
            if conv:
                return conv

        projet = self.get_projet(projet_id)
        title = f"Discussion — {projet.name}" if projet else "Discussion projet"
        conv = Conversation(
            id=generate_uuid(),
            user_id=user_id,
            projet_id=projet_id,
            title=title,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_project_conversations(self, projet_id: str, user_id: str) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.projet_id == projet_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    async def chat_with_projet(
        self,
        *,
        projet_id: str,
        message: str,
        conversation_id: Optional[str],
        user_id: str,
        user_name: Optional[str] = None,
    ) -> dict:
        """Envoie un message dans une discussion contextualisée au projet."""
        from core.utils import utcnow

        projet = self.get_projet(projet_id)
        if not projet:
            raise ValueError(f"Projet introuvable : {projet_id}")

        conversation = self._get_or_create_project_conversation(projet_id, conversation_id, user_id)

        user_message = Message(
            id=generate_uuid(),
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        self.db.add(user_message)
        self.db.commit()

        history = [
            {"role": m.role, "content": m.content}
            for m in conversation.messages
            if m.role in {"user", "assistant"}
        ]

        # Contexte projet injecté dans le system prompt
        project_context = (
            f"Tu assistes l'utilisateur sur le projet : «{projet.name}».\n"
            f"Description : {projet.description or 'Non précisée'}.\n"
            f"Statut : {projet.status}.\n"
        )

        projet_docs = self.list_projet_documents(projet_id)
        doc_ids = [d.id for d in projet_docs]

        answer = await self.chat_agent.answer(
            message,
            history=history,
            user_name=user_name,
            extra_context=project_context,
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

    async def suggest_next_steps(self, projet_id: str) -> str:
        """Demande à l'agent projet de suggérer les prochaines étapes pour un projet donné."""
        projet = self.get_projet(projet_id)
        if not projet:
            raise ValueError(f"Projet introuvable : {projet_id}")

        return await self.project_agent.suggest_next_steps(
            name=projet.name,
            description=projet.description or "",
            status=projet.status,
        )
