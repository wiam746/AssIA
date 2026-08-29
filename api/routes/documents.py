"""Routes de gestion des documents : upload, listing, consultation, suppression et discussions dédiées."""

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from api.dependencies import CurrentUser, DocumentServiceDep
from models.schemas import ConversationRead, DocumentChatCreate, DocumentRead, DocumentUploadResponse
from services.document_service import DocumentService, DocumentValidationError

router = APIRouter(prefix="/documents", tags=["Documents"])


async def _run_indexation(document_service: DocumentService, document_id: str) -> None:
    """Tache de fond : indexe le document dans le vector store apres l'upload."""
    document = document_service.get_document(document_id)
    if document:
        await document_service._process_document(document)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> DocumentUploadResponse:
    """
    Uploade un document et retourne immediatement avec status='pending'.
    L'indexation (extraction + embeddings + vector store) tourne en arriere-plan.
    """
    file_bytes = await file.read()

    try:
        document = document_service.save_upload(
            file_bytes=file_bytes,
            original_filename=file.filename or "document",
            content_type=file.content_type,
            uploaded_by=current_user.id,
        )
    except DocumentValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    background_tasks.add_task(_run_indexation, document_service, document.id)

    return DocumentUploadResponse(
        document=DocumentRead.model_validate(document),
        message="Document recu, indexation en cours en arriere-plan.",
    )


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
) -> list[DocumentRead]:
    """Liste les documents uploades par l'utilisateur courant."""
    documents = document_service.list_documents(uploaded_by=current_user.id)
    return [DocumentRead.model_validate(d) for d in documents]


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(document_id: str, document_service: DocumentServiceDep) -> DocumentRead:
    """Recupere les details d'un document."""
    document = document_service.get_document(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: str, document_service: DocumentServiceDep) -> None:
    """Supprime un document (base, disque et vector store)."""
    deleted = await document_service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable.")


# ---------------------------------------------------------------------------
# Discussions / Chat spécifiques à un document
# ---------------------------------------------------------------------------

@router.post("/{document_id}/chat", response_model=dict)
async def chat_with_document(
    document_id: str,
    payload: DocumentChatCreate,
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
) -> dict:
    """Envoie un message dans la discussion dédiée à ce document."""
    try:
        result = await document_service.chat_with_document(
            document_id=document_id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            user_id=current_user.id,
            user_name=current_user.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return result


@router.get("/{document_id}/conversations", response_model=list[ConversationRead])
async def list_document_conversations(
    document_id: str,
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
) -> list[ConversationRead]:
    """Liste les conversations de chat associées à ce document."""
    convs = document_service.list_document_conversations(document_id, current_user.id)
    return [ConversationRead.model_validate(c) for c in convs]
