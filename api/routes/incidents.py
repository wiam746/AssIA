"""Routes de gestion des incidents, de leurs documents et de leurs discussions."""

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile, status

from api.dependencies import CurrentUser, DocumentServiceDep, IncidentServiceDep
from models.schemas import (
    ConversationRead,
    DocumentRead,
    IncidentChatCreate,
    IncidentCreate,
    IncidentDocumentAdd,
    IncidentRead,
    IncidentUpdate,
)
from services.document_service import DocumentValidationError

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("", response_model=IncidentRead, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    incident_service: IncidentServiceDep,
    current_user: CurrentUser,
) -> IncidentRead:
    """Declare un nouvel incident et lance son analyse automatique via l'agent."""
    incident = await incident_service.create_incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        document_id=payload.document_id,
        reported_by=current_user.id,
    )
    return _to_read(incident, incident_service)


@router.get("", response_model=list[IncidentRead])
async def list_incidents(
    incident_service: IncidentServiceDep,
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[IncidentRead]:
    """Liste les incidents, avec filtre optionnel par statut."""
    incidents = incident_service.list_incidents(status=status_filter)
    return [_to_read(i, incident_service) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(incident_id: str, incident_service: IncidentServiceDep) -> IncidentRead:
    """Recupere le detail d'un incident, y compris son analyse et ses documents."""
    incident = incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident introuvable.")
    return _to_read(incident, incident_service)


@router.patch("/{incident_id}", response_model=IncidentRead)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    incident_service: IncidentServiceDep,
) -> IncidentRead:
    """Met a jour le statut (ouvert, en_cours, resolu, ferme) et/ou la resolution d'un incident."""
    incident = incident_service.update_incident(
        incident_id,
        status=payload.status,
        resolution=payload.resolution,
        document_id=payload.document_id,
    )
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident introuvable.")
    return _to_read(incident, incident_service)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(incident_id: str, incident_service: IncidentServiceDep) -> None:
    """Supprime un incident."""
    deleted = incident_service.delete_incident(incident_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident introuvable.")


# ---------------------------------------------------------------------------
# Documents de l'incident
# ---------------------------------------------------------------------------

@router.get("/{incident_id}/documents", response_model=list[DocumentRead])
async def list_incident_documents(
    incident_id: str,
    incident_service: IncidentServiceDep,
) -> list[DocumentRead]:
    """Liste tous les documents attachés à cet incident."""
    docs = incident_service.list_incident_documents(incident_id)
    return [DocumentRead.model_validate(d) for d in docs]


@router.post("/{incident_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def add_existing_document_to_incident(
    incident_id: str,
    payload: IncidentDocumentAdd,
    incident_service: IncidentServiceDep,
) -> DocumentRead:
    """Attache un document existant de la bibliothèque à cet incident."""
    link = incident_service.add_document_to_incident(incident_id, payload.document_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident ou document introuvable.",
        )
    return DocumentRead.model_validate(link.document)


@router.post("/{incident_id}/documents/upload", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_and_attach_incident_document(
    incident_id: str,
    background_tasks: BackgroundTasks,
    incident_service: IncidentServiceDep,
    document_service: DocumentServiceDep,
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> DocumentRead:
    """Upload un nouveau fichier, l'indexe et l'attache immédiatement à l'incident."""
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

    async def _run_indexation():
        doc = document_service.get_document(document.id)
        if doc:
            await document_service._process_document(doc)

    background_tasks.add_task(_run_indexation)
    incident_service.add_document_to_incident(incident_id, document.id)

    return DocumentRead.model_validate(document)


@router.delete("/{incident_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_document_from_incident(
    incident_id: str,
    document_id: str,
    incident_service: IncidentServiceDep,
) -> None:
    """Détache un document de l'incident."""
    removed = incident_service.remove_document_from_incident(incident_id, document_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lien document-incident introuvable.")


# ---------------------------------------------------------------------------
# Chat / Discussions de l'incident
# ---------------------------------------------------------------------------

@router.post("/{incident_id}/chat", response_model=dict)
async def chat_with_incident(
    incident_id: str,
    payload: IncidentChatCreate,
    incident_service: IncidentServiceDep,
    current_user: CurrentUser,
) -> dict:
    """Envoie un message dans la discussion contextualisée à cet incident."""
    try:
        result = await incident_service.chat_with_incident(
            incident_id=incident_id,
            message=payload.message,
            conversation_id=payload.conversation_id,
            user_id=current_user.id,
            user_name=current_user.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return result


@router.get("/{incident_id}/conversations", response_model=list[ConversationRead])
async def list_incident_conversations(
    incident_id: str,
    incident_service: IncidentServiceDep,
    current_user: CurrentUser,
) -> list[ConversationRead]:
    """Liste les conversations de chat associées à cet incident."""
    convs = incident_service.list_incident_conversations(incident_id, current_user.id)
    from models.schemas import ConversationRead as CR
    return [CR.model_validate(c) for c in convs]


# ---------------------------------------------------------------------------
# Helper interne
# ---------------------------------------------------------------------------

def _to_read(incident, incident_service: IncidentServiceDep) -> IncidentRead:
    docs = incident_service.list_incident_documents(incident.id)
    read = IncidentRead.model_validate(incident)
    read.documents = [DocumentRead.model_validate(d) for d in docs]
    return read
