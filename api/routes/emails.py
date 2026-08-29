"""Routes de redaction et d'analyse d'emails professionnels."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import CurrentUser, EmailServiceDep
from models.schemas import EmailDraftRead, EmailDraftRequest

router = APIRouter(prefix="/emails", tags=["Emails"])


class EmailAnalysisRequest(BaseModel):
    email_content: str = Field(..., min_length=1)


@router.post("/draft", response_model=EmailDraftRead, status_code=status.HTTP_201_CREATED)
async def draft_email(
    payload: EmailDraftRequest,
    email_service: EmailServiceDep,
    current_user: CurrentUser,
) -> EmailDraftRead:
    """Genere un brouillon d'email professionnel a partir d'instructions."""
    if payload.mode != "redaction":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Utilisez /emails/analyze pour le mode analyse.",
        )

    draft = await email_service.draft_email(
        instructions=payload.instructions,
        tone=payload.tone,
        recipient_name=payload.recipient_name,
        created_by=current_user.id,
    )
    return EmailDraftRead.model_validate(draft)


@router.post("/analyze", response_model=EmailDraftRead, status_code=status.HTTP_201_CREATED)
async def analyze_email(
    payload: EmailAnalysisRequest,
    email_service: EmailServiceDep,
    current_user: CurrentUser,
) -> EmailDraftRead:
    """Analyse un email recu et retourne une synthese structuree."""
    draft = await email_service.analyze_email(
        email_content=payload.email_content,
        created_by=current_user.id,
    )
    return EmailDraftRead.model_validate(draft)


@router.get("", response_model=list[EmailDraftRead])
async def list_drafts(
    email_service: EmailServiceDep,
    current_user: CurrentUser,
) -> list[EmailDraftRead]:
    """Liste les brouillons/analyses d'emails de l'utilisateur courant."""
    drafts = email_service.list_drafts(created_by=current_user.id)
    return [EmailDraftRead.model_validate(d) for d in drafts]


@router.get("/{draft_id}", response_model=EmailDraftRead)
async def get_draft(draft_id: str, email_service: EmailServiceDep) -> EmailDraftRead:
    """Recupere un brouillon ou une analyse d'email par son identifiant."""
    draft = email_service.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brouillon introuvable.")
    return EmailDraftRead.model_validate(draft)
