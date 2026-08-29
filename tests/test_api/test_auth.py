"""Tests des routes d'authentification — POST /api/auth/login et GET /api/auth/me."""

from unittest.mock import AsyncMock, patch


def test_health_check(client):
    """L'endpoint /health doit retourner status ok ou degraded."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "llm_provider" in data
    assert "vector_store_provider" in data


def test_root_endpoint(client):
    """L'endpoint racine / doit retourner le nom de l'application."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "app" in data


def test_get_me(client):
    """GET /api/auth/me doit retourner le profil de l'utilisateur authentifié."""
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True


def test_login_success():
    """POST /api/auth/login doit retourner un access_token en cas de succès."""
    from fastapi.testclient import TestClient
    from api.main import app

    mock_token_data = {
        "access_token": "fake-jwt-token",
        "refresh_token": "fake-refresh-token",
        "expires_in": 3600,
    }

    with patch(
        "api.routes.auth.exchange_credentials_for_token",
        new_callable=AsyncMock,
        return_value=mock_token_data,
    ):
        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "password"},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "fake-jwt-token"
    assert "expires_in" in data


def test_login_invalid_credentials():
    """POST /api/auth/login doit retourner 401 en cas d'identifiants invalides."""
    from fastapi.testclient import TestClient
    from api.main import app
    from api.auth import AuthError

    with patch(
        "api.routes.auth.exchange_credentials_for_token",
        new_callable=AsyncMock,
        side_effect=AuthError("Nom d'utilisateur ou mot de passe incorrect."),
    ):
        with TestClient(app) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": "wrong", "password": "wrong"},
            )

    assert response.status_code == 401
