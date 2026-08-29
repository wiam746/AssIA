"""
Schemas Pydantic utilises par l'API (validation des requetes / reponses).

Ces modeles sont distincts des modeles ORM (models/database.py) afin de
decoupler le contrat d'API de la structure de stockage en base.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ============================================================================
# Utilisateur
# ============================================================================


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    is_active: bool
    created_at: datetime


# ============================================================================
# Authentification
# ============================================================================


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None


# ============================================================================
# Documents
# ============================================================================


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    original_filename: str
    file_size: int
    content_type: Optional[str] = None
    status: Literal["pending", "processing", "indexed", "error"]
    error_message: Optional[str] = None
    created_at: datetime
    indexed_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    message: str = "Document recu, traitement en cours."


# ============================================================================
# Chat
# ============================================================================


class ChatMessageCreate(BaseModel):
    conversation_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=8000)
    document_id: Optional[str] = None
    document_ids: Optional[List[str]] = Field(default_factory=list)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    projet_id: Optional[str] = None
    incident_id: Optional[str] = None
    document_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = []


class DocumentChatCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageRead
    sources: List[str] = Field(default_factory=list)


# ============================================================================
# Reunions
# ============================================================================


ReunionStatus = Literal["brouillon", "valide"]


class ReunionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    meeting_date: Optional[datetime] = None
    participants: Optional[str] = None
    objet: Optional[str] = None
    raw_content: str = Field(..., min_length=1)
    document_id: Optional[str] = None


class ReunionUpdate(BaseModel):
    title: Optional[str] = None
    meeting_date: Optional[datetime] = None
    participants: Optional[str] = None
    objet: Optional[str] = None
    summary: Optional[str] = None
    decisions: Optional[str] = None
    actions: Optional[str] = None
    prochaine_reunion: Optional[str] = None
    status: Optional[ReunionStatus] = None
    document_id: Optional[str] = None


class ReunionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    meeting_date: Optional[datetime] = None
    participants: Optional[str] = None
    objet: Optional[str] = None
    summary: Optional[str] = None
    decisions: Optional[str] = None
    actions: Optional[str] = None
    prochaine_reunion: Optional[str] = None
    status: ReunionStatus = "brouillon"
    document_id: Optional[str] = None
    document: Optional[DocumentRead] = None
    created_at: datetime


# ============================================================================
# Incidents
# ============================================================================


IncidentSeverity = Literal["mineur", "majeur", "critique"]
IncidentStatus = Literal["ouvert", "en_cours", "resolu", "ferme"]


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    severity: IncidentSeverity = "mineur"
    document_id: Optional[str] = None


class IncidentUpdate(BaseModel):
    status: Optional[IncidentStatus] = None
    resolution: Optional[str] = None
    document_id: Optional[str] = None


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    analysis: Optional[str] = None
    resolution: Optional[str] = None
    document_id: Optional[str] = None
    document: Optional[DocumentRead] = None
    documents: List[DocumentRead] = []
    created_at: datetime
    resolved_at: Optional[datetime] = None


class IncidentDocumentAdd(BaseModel):
    document_id: str


class IncidentChatCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[str] = None


# ============================================================================
# Projets
# ============================================================================


ProjetStatus = Literal["actif", "en_pause", "termine", "archive"]


class ProjetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    document_id: Optional[str] = None


class ProjetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjetStatus] = None
    document_id: Optional[str] = None


class ProjetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    status: ProjetStatus
    document_id: Optional[str] = None
    document: Optional[DocumentRead] = None
    documents: List[DocumentRead] = []  # tous les documents attachés via projet_documents
    created_at: datetime
    updated_at: datetime


class ProjetDocumentAdd(BaseModel):
    document_id: str


class ProjetChatCreate(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[str] = None


# ============================================================================
# Emails
# ============================================================================


EmailTone = Literal["formel", "neutre", "cordial"]
EmailMode = Literal["redaction", "analyse"]


class EmailDraftRequest(BaseModel):
    mode: EmailMode = "redaction"
    tone: EmailTone = "neutre"
    instructions: str = Field(..., min_length=1, description="Instructions ou contenu source")
    recipient_name: Optional[str] = None


class EmailDraftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject: Optional[str] = None
    body: str
    tone: EmailTone
    mode: EmailMode
    created_at: datetime


# ============================================================================
# Generique
# ============================================================================


class ErrorResponse(BaseModel):
    detail: str


class HealthCheckResponse(BaseModel):
    status: Literal["ok", "degraded", "down"]
    llm_provider: str
    vector_store_provider: str
    version: str = "1.0.0"
