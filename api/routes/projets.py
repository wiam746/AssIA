"""Routes de gestion des projets : CRUD, documents associés et chat contextualisé."""

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status

from api.dependencies import CurrentUser, DocumentServiceDep, ProjetServiceDep
from models.schemas import (
    ConversationRead,
    DocumentRead,
    ProjetChatCreate,
    ProjetCreate,
    ProjetDocumentAdd,
    ProjetRead,
    ProjetUpdate,
)
from services.document_service import DocumentValidationError

router = APIRouter(prefix="/projets", tags=["Projets"])


@router.post("", response_model=ProjetRead, status_code=status.HTTP_201_CREATED)
async def create_projet(
    payload: ProjetCreate,
    projet_service: ProjetServiceDep,
    current_user: CurrentUser,
) -> ProjetRead:
    """Cree un nouveau projet."""
    projet = projet_service.create_projet(
        name=payload.name,
        description=payload.description,
        document_id=payload.document_id,
        owner_id=current_user.id,
    )
    return _to_read(projet, projet_service)


@router.get("", response_model=list[ProjetRead])
async def list_projets(
    projet_service: ProjetServiceDep,
    current_user: CurrentUser,
) -> list[ProjetRead]:
    """Liste les projets de l'utilisateur courant."""
    projets = projet_service.list_projets(owner_id=current_user.id)
    return [_to_read(p, projet_service) for p in projets]


@router.get("/{projet_id}", response_model=ProjetRead)
async def get_projet(projet_id: str, projet_service: ProjetServiceDep) -> ProjetRead:
    """Recupere le detail d'un projet."""
    projet = projet_service.get_projet(projet_id)
    if not projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable.")
    return _to_read(projet, projet_service)


@router.patch("/{projet_id}", response_model=ProjetRead)
async def update_projet(
    projet_id: str,
    payload: ProjetUpdate,
    projet_service: ProjetServiceDep,
) -> ProjetRead:
    """Met a jour un projet (nom, description, statut)."""
    projet = projet_service.update_projet(
        projet_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        document_id=payload.document_id,
    )
    if not projet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable.")
    return _to_read(projet, projet_service)


@router.delete("/{projet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_projet(projet_id: str, projet_service: ProjetServiceDep) -> None:
    """Supprime un projet."""
    deleted = projet_service.delete_projet(projet_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet introuvable.")


@router.post("/{projet_id}/suggestions", response_model=dict)
async def suggest_next_steps(projet_id: str, projet_service: ProjetServiceDep) -> dict:
    """Demande a l'agent projet de suggerer les prochaines etapes pour ce projet."""
    try:
        suggestions = await projet_service.suggest_next_steps(projet_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"projet_id": projet_id, "suggestions": suggestions}


# ---------------------------------------------------------------------------
# Documents du projet
# ---------------------------------------------------------------------------

@router.get("/{projet_id}/documents", response_model=list[DocumentRead])
async def list_projet_documents(
    projet_id: str,
    projet_service: ProjetServiceDep,
) -> list[DocumentRead]:
    """Liste tous les documents attachés à ce projet."""
    docs = projet_service.list_projet_documents(projet_id)
    return [DocumentRead.model_validate(d) for d in docs]


@router.post("/{projet_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def add_existing_document(
    projet_id: str,
    payload: ProjetDocumentAdd,
    projet_service: ProjetServiceDep,
) -> DocumentRead:
    """Attache un document existant de la bibliothèque à ce projet."""
    link = projet_service.add_document_to_projet(projet_id, payload.document_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet ou document introuvable.",
        )
    return DocumentRead.model_validate(link.document)


@router.post("/{projet_id}/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_and_attach_document(
    projet_id: str,
    background_tasks: BackgroundTasks,
    projet_service: ProjetServiceDep,
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> DocumentRead:
    """Upload un nouveau fichier, l'indexe en bibliothèque et l'attache immédiatement au projet."""
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

    # Indexation en arrière-plan
    async def _run_indexation():
        doc = document_service.get_document(document.id)
        if doc:
            await document_service._process_document(doc)

    background_tasks.add_task(_run_indexation)

    # Attacher au projet
    projet_service.add_document_to_projet(projet_id, document.id)

    return DocumentRead.model_validate(document)


@router.delete("/{projet_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document_from_projet(
    projet_id: str,
    document_id: str,
    projet_service: ProjetServiceDep,
) -> None:
    """Détache un document du projet (ne supprime pas le document de la bibliothèque)."""
    removed = projet_service.remove_document_from_projet(projet_id, document_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien document-projet introuvable.")


# ---------------------------------------------------------------------------
# Chat / Discussion du projet
# ---------------------------------------------------------------------------

@router.post("/{projet_id}/chat", response_model=dict)
async def chat_with_projet(
    projet_id: str,
    payload: ProjetChatCreate,
    projet_service: ProjetServiceDep,
    current_user: CurrentUser,
) -> dict:
    """Envoie un message dans la discussion contextualisée au projet."""
    try:
        result = await projet_service.chat_with_projet(
            projet_id=projet_id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            user_id=current_user.id,
            user_name=current_user.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return result


@router.get("/{projet_id}/conversations", response_model=list[ConversationRead])
async def list_project_conversations(
    projet_id: str,
    projet_service: ProjetServiceDep,
    current_user: CurrentUser,
) -> list[ConversationRead]:
    """Liste les conversations de chat associées à ce projet."""
    convs = projet_service.list_project_conversations(projet_id, current_user.id)
    from models.schemas import ConversationRead as CR, MessageRead
    return [CR.model_validate(c) for c in convs]


# ---------------------------------------------------------------------------
# Helper interne
# ---------------------------------------------------------------------------

def _to_read(projet, projet_service: ProjetServiceDep) -> ProjetRead:
    """Construit un ProjetRead en incluant la liste des documents attachés."""
    docs = projet_service.list_projet_documents(projet.id)
    read = ProjetRead.model_validate(projet)
    read.documents = [DocumentRead.model_validate(d) for d in docs]
    return read
