"""
Service de gestion du cycle de vie des documents : upload, stockage sur disque,
suivi du statut en base, déclenchement de l'indexation RAG et discussions dédiées.
"""

import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from agents.chat_agent import ChatAgent
from config.settings import settings
from core.utils import bytes_to_human_readable, generate_uuid, unique_storage_filename, utcnow
from models.database import Conversation, Document, Message
from services.rag_service import RagService

logger = logging.getLogger("services.document_service")


class DocumentValidationError(Exception):
    """Levee lorsque le fichier uploade ne respecte pas les contraintes autorisees."""


class DocumentService:
    """Orchestration de l'upload, du stockage, de l'indexation et des discussions sur les documents."""

    def __init__(
        self,
        db: Session,
        rag_service: Optional[RagService] = None,
        chat_agent: Optional[ChatAgent] = None,
    ) -> None:
        self.db = db
        self.rag_service = rag_service or RagService()
        self.chat_agent = chat_agent or ChatAgent()
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_upload(self, original_filename: str, file_size: int) -> None:
        extension = Path(original_filename).suffix.lower()
        if extension not in settings.allowed_extensions_list:
            raise DocumentValidationError(
                f"Extension '{extension}' non autorisee. "
                f"Extensions acceptees : {settings.allowed_extensions_list}"
            )

        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise DocumentValidationError(
                f"Fichier trop volumineux ({bytes_to_human_readable(file_size)}). "
                f"Taille maximale autorisee : {settings.max_upload_size_mb} Mo."
            )

    def save_upload(
        self,
        *,
        file_bytes: bytes,
        original_filename: str,
        content_type: Optional[str],
        uploaded_by: Optional[str] = None,
    ) -> Document:
        self._validate_upload(original_filename, len(file_bytes))

        document_id = generate_uuid()
        stored_filename = unique_storage_filename(original_filename)
        destination = self.upload_dir / stored_filename
        destination.write_bytes(file_bytes)

        document = Document(
            id=document_id,
            filename=stored_filename,
            original_filename=original_filename,
            file_path=str(destination),
            file_size=len(file_bytes),
            content_type=content_type,
            status="pending",
            uploaded_by=uploaded_by,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        logger.info("Document '%s' sauvegarde, indexation en attente.", document_id)
        return document

    async def _process_document(self, document: Document) -> None:
        """Extrait le texte, indexe les chunks dans le vector store et met a jour le statut."""
        document.status = "processing"
        self.db.commit()

        try:
            nb_chunks = await self.rag_service.index_document(
                document.file_path,
                document_id=document.id,
                metadata={
                    "original_filename": document.original_filename,
                    "content_type": document.content_type or "",
                },
            )
            document.status = "indexed"
            document.indexed_at = utcnow()
            logger.info("Document '%s' indexe avec succes (%d chunks).", document.id, nb_chunks)
        except Exception as exc:
            document.status = "error"
            document.error_message = str(exc)
            logger.error("Echec de l'indexation du document '%s' : %s", document.id, exc)
        finally:
            self.db.commit()

    def list_documents(self, uploaded_by: Optional[str] = None) -> List[Document]:
        query = self.db.query(Document)
        if uploaded_by:
            query = query.filter(Document.uploaded_by == uploaded_by)
        return query.order_by(Document.created_at.desc()).all()

    def get_document(self, document_id: str) -> Optional[Document]:
        return self.db.query(Document).filter(Document.id == document_id).first()

    async def delete_document(self, document_id: str) -> bool:
        document = self.get_document(document_id)
        if not document:
            return False

        probable_chunk_ids = [f"{document.id}_chunk_{i}" for i in range(500)]
        await self.rag_service.remove_document(document.id, probable_chunk_ids)

        file_path = Path(document.file_path)
        if file_path.exists():
            file_path.unlink()

        self.db.delete(document)
        self.db.commit()
        logger.info("Document '%s' supprime.", document_id)
        return True

    # -----------------------------------------------------------------------
    # Discussions contextualisées sur un Document
    # -----------------------------------------------------------------------

    def _get_or_create_document_conversation(
        self, document_id: str, conversation_id: Optional[str], user_id: str
    ) -> Conversation:
        if conversation_id:
            conv = (
                self.db.query(Conversation)
                .filter(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                    Conversation.document_id == document_id,
                )
                .first()
            )
            if conv:
                return conv

        doc = self.get_document(document_id)
        title = f"Discussion — {doc.original_filename}" if doc else "Discussion document"
        conv = Conversation(
            id=generate_uuid(),
            user_id=user_id,
            document_id=document_id,
            title=title,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def list_document_conversations(self, document_id: str, user_id: str) -> List[Conversation]:
        return (
            self.db.query(Conversation)
            .filter(
                Conversation.document_id == document_id,
                Conversation.user_id == user_id,
            )
            .order_by(Conversation.updated_at.desc())
            .all()
        )

    async def chat_with_document(
        self,
        *,
        document_id: str,
        message: str,
        conversation_id: Optional[str],
        user_id: str,
        user_name: Optional[str] = None,
    ) -> dict:
        """Envoie un message dans la discussion dédiée à ce document."""
        doc = self.get_document(document_id)
        if not doc:
            raise ValueError(f"Document introuvable : {document_id}")

        conversation = self._get_or_create_document_conversation(document_id, conversation_id, user_id)

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

        doc_context = (
            f"Tu réponds aux questions spécifiques au document : «{doc.original_filename}».\n"
            f"Taille du fichier : {doc.file_size} octets | Statut d'indexation : {doc.status}.\n"
        )

        answer = await self.chat_agent.answer(
            message,
            history=history,
            user_name=user_name,
            extra_context=doc_context,
            document_id=document_id,
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
