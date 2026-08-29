"""
Authentification basee sur Keycloak (OIDC / JWT).

Valide les tokens JWT emis par Keycloak (verification via JWKS), extrait
l'identite de l'utilisateur et synchronise une entree locale en base
pour faciliter les relations avec les autres tables (documents, conversations...).
"""

import logging
from functools import lru_cache
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import settings
from models.database import User, get_db

logger = logging.getLogger("api.auth")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=(
        f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
        f"/protocol/openid-connect/token"
    ),
    auto_error=True,
)


class AuthError(HTTPException):
    """Erreur d'authentification renvoyee au client avec le code 401."""

    def __init__(self, detail: str = "Identifiants invalides ou expires.") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@lru_cache
def _get_jwks() -> Dict[str, Any]:
    """Recupere (et met en cache) le trousseau de cles publiques (JWKS) de Keycloak."""
    jwks_url = (
        f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
        f"/protocol/openid-connect/certs"
    )
    try:
        response = httpx.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as exc:
        logger.error("Impossible de recuperer le JWKS Keycloak : %s", exc)
        raise AuthError("Service d'authentification indisponible.") from exc


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode et verifie un token JWT emis par Keycloak."""
    jwks = _get_jwks()

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise AuthError("Token malforme.") from exc

    key = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    if key is None:
        raise AuthError("Cle de signature inconnue.")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.keycloak_client_id,
            options={"verify_aud": False},  # Keycloak n'inclut pas toujours l'audience attendue
        )
        return payload
    except JWTError as exc:
        raise AuthError(f"Token invalide : {exc}") from exc


def _get_or_create_user(db: Session, payload: Dict[str, Any]) -> User:
    """Synchronise l'utilisateur Keycloak (payload du token) avec la table locale `users`."""
    user_id = payload.get("sub")
    email = payload.get("email") or f"{user_id}@inconnu.local"
    full_name = payload.get("name") or payload.get("preferred_username")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        # Fallback par email si l'utilisateur a ete recree dans Keycloak sous un nouvel ID (sub)
        user = db.query(User).filter(User.email == email).first()
        if user is not None:
            user.id = user_id
            if full_name:
                user.full_name = full_name
        else:
            user = User(id=user_id, email=email, full_name=full_name, is_active=True)
            db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Utilisateur synchronise depuis Keycloak : %s", email)
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependance FastAPI retournant l'utilisateur authentifie courant."""
    payload = decode_access_token(token)
    user = _get_or_create_user(db, payload)

    if not user.is_active:
        raise AuthError("Compte utilisateur desactive.")

    return user


async def _find_keycloak_username_for_input(search_term: str) -> Optional[str]:
    """
    Tente de resoudre un identifiant libre (prenom, nom, pseudo) vers un username
    Keycloak valide, en interrogeant l'API Admin.
    Retourne le username Keycloak si trouve, sinon None.
    """
    try:
        admin_token = await _get_admin_token()
        headers = {"Authorization": f"Bearer {admin_token}"}
        users_url = (
            f"{settings.keycloak_server_url}/admin/realms/{settings.keycloak_realm}/users"
        )
        # Keycloak cherche dans username, email, firstName, lastName avec &search=
        search_url = f"{users_url}?search={search_term}&max=5"
        async with httpx.AsyncClient() as client:
            resp = await client.get(search_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            users = resp.json()
            if len(users) == 1:
                # Un seul résultat : on peut s'y fier
                return users[0].get("username")
            # Plusieurs résultats : chercher une correspondance exacte
            term_lower = search_term.lower()
            for u in users:
                if (
                    u.get("username", "").lower() == term_lower
                    or u.get("firstName", "").lower() == term_lower
                    or u.get("lastName", "").lower() == term_lower
                    or (u.get("email") or "").lower() == term_lower
                ):
                    return u.get("username")
    except Exception:
        pass
    return None


async def exchange_credentials_for_token(
    username: str, password: str, db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Echange un couple identifiant/mot de passe contre un token Keycloak.
    Supporte : adresse e-mail, username Keycloak, prefixe d'email, prenom, nom.
    """
    token_url = (
        f"{settings.keycloak_server_url}/realms/{settings.keycloak_realm}"
        f"/protocol/openid-connect/token"
    )

    async def _try_token(u: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": settings.keycloak_client_id,
                    "client_secret": settings.keycloak_client_secret,
                    "username": u,
                    "password": password,
                },
                timeout=10,
            )
        return resp.json() if resp.status_code == 200 else None

    # 1. Tentative directe avec l'identifiant fourni (email complet ou username)
    result = await _try_token(username)
    if result:
        return result

    # 2. Si c'est un email, tenter avec le préfixe (avant @)
    if "@" in username:
        prefix = username.split("@")[0].lower()
        result = await _try_token(prefix)
        if result:
            return result

    # 3. Recherche dans Keycloak par prénom / nom / username partiel
    kc_username = await _find_keycloak_username_for_input(username)
    if kc_username and kc_username.lower() != username.lower():
        result = await _try_token(kc_username)
        if result:
            return result

    logger.warning("Echec d'authentification Keycloak pour '%s'.", username)
    raise AuthError("Nom d'utilisateur ou mot de passe incorrect.")



async def _get_admin_token() -> str:
    """Obtient un token d'acces admin Keycloak via le realm 'master'."""
    token_url = f"{settings.keycloak_server_url}/realms/master/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": settings.keycloak_admin_user,
        "password": settings.keycloak_admin_password,
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, data=data, timeout=10)

    if response.status_code != 200:
        logger.error("Impossible d'obtenir le token admin Keycloak : %s", response.text)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service d'authentification indisponible.",
        )
    return response.json()["access_token"]


async def register_user_in_keycloak(
    email: str, password: str, full_name: Optional[str] = None
) -> None:
    """
    Cree un nouvel utilisateur dans le realm Keycloak via l'API Admin REST,
    puis definit son mot de passe via /reset-password (plus fiable que le
    champ credentials dans le payload de creation).
    Leve une HTTPException 409 si l'email est deja utilise.
    """
    admin_token = await _get_admin_token()
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

    users_url = (
        f"{settings.keycloak_server_url}/admin/realms/{settings.keycloak_realm}/users"
    )

    # Tente d'utiliser la partie avant le @ comme username pour Keycloak, ou l'email complet
    preferred_username = email.split("@")[0].lower()

    if full_name and full_name.strip():
        parts = full_name.strip().split(" ", 1)
        first_name = parts[0]
        last_name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else parts[0]
    else:
        first_name = preferred_username
        last_name = preferred_username

    payload: Dict[str, Any] = {
        "username": preferred_username,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "enabled": True,
        "emailVerified": True,
        "requiredActions": [],
        "credentials": [
            {"type": "password", "value": password, "temporary": False}
        ],
    }

    async with httpx.AsyncClient() as client:
        # 1. Creer l'utilisateur avec representation complete
        create_resp = await client.post(users_url, json=payload, headers=headers, timeout=10)

        # Si le pseudo est deja pris, essayer avec l'email complet comme username Keycloak
        if create_resp.status_code == 409:
            payload["username"] = email.lower()
            create_resp = await client.post(users_url, json=payload, headers=headers, timeout=10)

            if create_resp.status_code == 409:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Un compte avec cet email existe deja.",
                )

        if create_resp.status_code not in (200, 201):
            logger.error(
                "Echec de creation utilisateur Keycloak : %s %s",
                create_resp.status_code, create_resp.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Impossible de creer le compte. Veuillez reessayer.",
            )

        # 2. Recuperer l'ID du nouvel utilisateur depuis le header Location
        # Ex: .../admin/realms/AssIA/users/<uuid>
        location = create_resp.headers.get("Location", "")
        user_id = location.rstrip("/").split("/")[-1]

        if not user_id:
            # Fallback : rechercher par email
            search_resp = await client.get(
                f"{users_url}?email={email}&exact=true",
                headers=headers,
                timeout=10,
            )
            users = search_resp.json()
            if not users:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Utilisateur cree mais introuvable pour definir le mot de passe.",
                )
            user_id = users[0]["id"]

        # 3. S'assurer que le mot de passe est fixe via reset-password
        pwd_url = f"{users_url}/{user_id}/reset-password"
        pwd_resp = await client.put(
            pwd_url,
            json={"type": "password", "value": password, "temporary": False},
            headers=headers,
            timeout=10,
        )

        if pwd_resp.status_code not in (200, 204):
            logger.error(
                "Echec de definition du mot de passe Keycloak : %s %s",
                pwd_resp.status_code, pwd_resp.text,
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Compte cree mais mot de passe non defini. Contactez un administrateur.",
            )

        # 4. S'assurer que le profil conserve username, email et requiredActions vides
        update_user_url = f"{users_url}/{user_id}"
        payload["requiredActions"] = []
        await client.put(
            update_user_url,
            json=payload,
            headers=headers,
            timeout=10,
        )

    logger.info("Nouvel utilisateur Keycloak cree avec mot de passe : %s", email)


async def request_password_reset(email_or_username: str) -> dict:
    """
    Envoie une demande de reinitialisation de mot de passe Keycloak.
    Tente d'envoyer l'email Keycloak execute-actions-email (UPDATE_PASSWORD).
    """
    try:
        admin_token = await _get_admin_token()
        headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        users_url = f"{settings.keycloak_server_url}/admin/realms/{settings.keycloak_realm}/users"

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{users_url}?search={email_or_username}", headers=headers, timeout=10)
            if resp.status_code == 200:
                users = resp.json()
                if users:
                    user_id = users[0]["id"]
                    # Tentative d'envoi d'email de réinitialisation Keycloak
                    reset_url = f"{users_url}/{user_id}/execute-actions-email"
                    await client.put(reset_url, json=["UPDATE_PASSWORD"], headers=headers, timeout=10)
                    return {"message": "Si l'adresse existe, un e-mail de réinitialisation a été envoyé."}

        return {"message": "Si l'adresse existe, un e-mail de réinitialisation a été envoyé."}
    except Exception as exc:
        logger.warning("Erreur lors de la demande de reset de mot de passe : %s", exc)
        return {"message": "Si l'adresse existe, un e-mail de réinitialisation a été envoyé."}


