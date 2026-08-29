"""Routes de gestion des comptes-rendus de reunion."""

from typing import Literal
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from api.dependencies import CurrentUser, ReunionServiceDep
from models.schemas import ReunionCreate, ReunionRead, ReunionUpdate
from services.export_service import generate_reunion_docx, generate_reunion_pdf

router = APIRouter(prefix="/reunions", tags=["Reunions"])


@router.post("", response_model=ReunionRead, status_code=status.HTTP_201_CREATED)
async def create_reunion(
    payload: ReunionCreate,
    reunion_service: ReunionServiceDep,
    current_user: CurrentUser,
) -> ReunionRead:
    """Cree un compte-rendu de reunion, l'analyse via l'agent et le sauvegarde en brouillon."""
    reunion = await reunion_service.create_reunion(
        title=payload.title,
        raw_content=payload.raw_content,
        meeting_date=payload.meeting_date,
        participants=payload.participants,
        objet=payload.objet,
        document_id=payload.document_id,
        created_by=current_user.id,
    )
    return ReunionRead.model_validate(reunion)


@router.get("", response_model=list[ReunionRead])
async def list_reunions(
    reunion_service: ReunionServiceDep,
    current_user: CurrentUser,
) -> list[ReunionRead]:
    """Liste les reunions creees par l'utilisateur courant."""
    reunions = reunion_service.list_reunions(created_by=current_user.id)
    return [ReunionRead.model_validate(r) for r in reunions]


@router.get("/{reunion_id}", response_model=ReunionRead)
async def get_reunion(reunion_id: str, reunion_service: ReunionServiceDep) -> ReunionRead:
    """Recupere le detail d'une reunion."""
    reunion = reunion_service.get_reunion(reunion_id)
    if not reunion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunion introuvable.")
    return ReunionRead.model_validate(reunion)


@router.patch("/{reunion_id}", response_model=ReunionRead)
async def update_reunion(
    reunion_id: str,
    payload: ReunionUpdate,
    reunion_service: ReunionServiceDep,
) -> ReunionRead:
    """Met a jour les champs d'un proces-verbal et/ou le valide (Validation Humaine)."""
    reunion = reunion_service.update_reunion(
        reunion_id,
        title=payload.title,
        meeting_date=payload.meeting_date,
        participants=payload.participants,
        objet=payload.objet,
        summary=payload.summary,
        decisions=payload.decisions,
        actions=payload.actions,
        prochaine_reunion=payload.prochaine_reunion,
        status=payload.status,
        document_id=payload.document_id,
    )
    if not reunion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunion introuvable.")
    return ReunionRead.model_validate(reunion)


@router.get("/{reunion_id}/export")
async def export_reunion(
    reunion_id: str,
    reunion_service: ReunionServiceDep,
    export_format: Literal["pdf", "docx"] = Query("pdf", alias="format"),
):
    """Exporte le compte-rendu de reunion au format Word (.docx) ou PDF (.pdf)."""
    reunion = reunion_service.get_reunion(reunion_id)
    if not reunion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunion introuvable.")

    safe_title = "".join(c if c.isalnum() or c in (" ", "_", "-") else "" for c in reunion.title).replace(" ", "_")

    if export_format == "docx":
        stream = generate_reunion_docx(reunion)
        headers = {"Content-Disposition": f'attachment; filename="Proces_Verbal_{safe_title}.docx"'}
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers=headers,
        )
    else:
        stream = generate_reunion_pdf(reunion)
        headers = {"Content-Disposition": f'attachment; filename="Proces_Verbal_{safe_title}.pdf"'}
        return StreamingResponse(
            stream,
            media_type="application/pdf",
            headers=headers,
        )


@router.delete("/{reunion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reunion(reunion_id: str, reunion_service: ReunionServiceDep) -> None:
    """Supprime une reunion."""
    deleted = reunion_service.delete_reunion(reunion_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reunion introuvable.")
