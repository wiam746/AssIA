from fastapi import APIRouter, Depends

from api.auth import (
    exchange_credentials_for_token,
    register_user_in_keycloak,
    request_password_reset,
)
from api.dependencies import CurrentUser
from models.database import get_db
from models.schemas import LoginRequest, RegisterRequest, TokenResponse, UserRead
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter(prefix="/auth", tags=["Authentification"])


class ForgotPasswordRequest(BaseModel):
    email: str


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Echange un identifiant/mot de passe contre un token d'acces Keycloak."""
    token_data = await exchange_credentials_for_token(payload.username, payload.password, db=db)
    return TokenResponse(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_in=token_data.get("expires_in", 0),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Cree un nouveau compte dans Keycloak puis connecte l'utilisateur immediatement."""
    await register_user_in_keycloak(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    # Connexion automatique apres creation (tente avec l'email, puis avec le prefixe si besoin)
    try:
        token_data = await exchange_credentials_for_token(payload.email, payload.password, db=db)
    except Exception:
        username = payload.email.split("@")[0].lower()
        token_data = await exchange_credentials_for_token(username, payload.password, db=db)

    return TokenResponse(
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        expires_in=token_data.get("expires_in", 0),
    )


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest):
    """Envoie une demande de reinitialisation de mot de passe."""
    return await request_password_reset(payload.email)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser) -> UserRead:
    """Retourne le profil de l'utilisateur actuellement authentifie."""
    return UserRead.model_validate(current_user)

