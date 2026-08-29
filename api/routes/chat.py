"""Routes de chat conversationnel (RAG) : envoi de messages et historique de conversations."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from agents.chat_agent import ChatAgent
from api.dependencies import CurrentUser, DbSession
from core.utils import generate_uuid, utcnow
from models.database import Conversation, Message
from models.schemas import ChatMessageCreate, ChatResponse, ConversationRead, MessageRead

router = APIRouter(prefix="/chat", tags=["Chat"])

_chat_agent = ChatAgent()


def _get_or_create_conversation(
    db: Session, conversation_id: str | None, user_id: str
) -> Conversation:
    if conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable."
            )
        return conversation

    conversation = Conversation(id=generate_uuid(), user_id=user_id, title="Nouvelle conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.post("/messages", response_model=ChatResponse)
async def send_message(
    payload: ChatMessageCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> ChatResponse:
    """Envoie un message a l'assistant et retourne sa reponse, avec les sources utilisees."""
    conversation = _get_or_create_conversation(db, payload.conversation_id, current_user.id)

    user_message = Message(
        id=generate_uuid(),
        conversation_id=conversation.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    db.commit()

    # Met a jour le titre de la conversation s'il est par defaut
    if conversation.title in {"Nouvelle conversation", "Nouvelle conversation"} and payload.message:
        title_text = payload.message.strip()
        conversation.title = title_text[:35] + ("..." if len(title_text) > 35 else "")

    history = [
        {"role": m.role, "content": m.content}
        for m in conversation.messages
        if m.role in {"user", "assistant"}
    ]

    answer = await _chat_agent.answer(
        payload.message,
        history=history,
        user_name=current_user.full_name,
        document_id=payload.document_id,
        document_ids=payload.document_ids if payload.document_ids else None,
    )

    assistant_message = Message(
        id=generate_uuid(),
        conversation_id=conversation.id,
        role="assistant",
        content=answer.content,
    )
    db.add(assistant_message)
    conversation.updated_at = utcnow()
    db.commit()
    db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation.id,
        message=MessageRead.model_validate(assistant_message),
        sources=answer.sources,
    )


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(db: DbSession, current_user: CurrentUser) -> list[ConversationRead]:
    """Liste les conversations de l'utilisateur courant."""
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [ConversationRead.model_validate(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: str, db: DbSession, current_user: CurrentUser
) -> ConversationRead:
    """Recupere une conversation avec l'ensemble de ses messages."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable.")

    return ConversationRead.model_validate(conversation)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(conversation_id: str, db: DbSession, current_user: CurrentUser) -> None:
    """Supprime une conversation et tous ses messages."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation introuvable.")

    db.delete(conversation)
    db.commit()
