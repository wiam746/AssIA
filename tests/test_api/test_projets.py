"""Tests des routes Projets — CRUD complet."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_projet(
    id_="proj-001",
    name="Migration Cloud",
    status="actif",
    owner_id="test-user-id-12345",
):
    from models.database import Projet

    return Projet(
        id=id_,
        name=name,
        description="Migration vers le cloud AWS.",
        status=status,
        owner_id=owner_id,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


def test_list_projets_empty(client):
    """GET /api/projets retourne une liste vide initialement."""
    response = client.get("/api/projets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_projets_with_data(client, db_session):
    """GET /api/projets retourne les projets de l'utilisateur."""
    proj = _make_projet()
    db_session.add(proj)
    db_session.commit()

    response = client.get("/api/projets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Migration Cloud"


def test_list_projets_only_own(client, db_session):
    """GET /api/projets ne retourne que les projets de l'utilisateur courant."""
    own = _make_projet(id_="p-own", name="Mon Projet", owner_id="test-user-id-12345")
    other = _make_projet(id_="p-other", name="Autre Projet", owner_id="autre-user-id")
    db_session.add(own)
    db_session.add(other)
    db_session.commit()

    response = client.get("/api/projets")
    assert response.status_code == 200
    # Seul le projet de l'utilisateur courant doit apparaître
    names = [p["name"] for p in response.json()]
    assert "Mon Projet" in names
    assert "Autre Projet" not in names


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_projet_not_found(client):
    """GET /api/projets/{id} retourne 404 si le projet n'existe pas."""
    response = client.get("/api/projets/inexistant-id")
    assert response.status_code == 404


def test_get_projet_existing(client, db_session):
    """GET /api/projets/{id} retourne le détail d'un projet existant."""
    proj = _make_projet(id_="p-detail")
    db_session.add(proj)
    db_session.commit()

    response = client.get("/api/projets/p-detail")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "p-detail"
    assert data["name"] == "Migration Cloud"
    assert data["status"] == "actif"


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


def test_create_projet(client):
    """POST /api/projets crée un projet et retourne 201."""
    response = client.post(
        "/api/projets",
        json={
            "name": "Refonte Site Web",
            "description": "Nouveau design React.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Refonte Site Web"
    assert data["status"] == "actif"


def test_create_projet_missing_name(client):
    """POST /api/projets retourne 422 si le nom est absent."""
    response = client.post("/api/projets", json={"description": "Sans nom"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_projet_not_found(client):
    """PATCH /api/projets/{id} retourne 404 si le projet n'existe pas."""
    response = client.patch("/api/projets/inexistant-id", json={"status": "termine"})
    assert response.status_code == 404


def test_update_projet_status(client, db_session):
    """PATCH /api/projets/{id} met à jour le statut d'un projet."""
    proj = _make_projet(id_="p-upd")
    db_session.add(proj)
    db_session.commit()

    response = client.patch("/api/projets/p-upd", json={"status": "en_pause"})
    assert response.status_code == 200
    assert response.json()["status"] == "en_pause"


def test_update_projet_name(client, db_session):
    """PATCH /api/projets/{id} met à jour le nom d'un projet."""
    proj = _make_projet(id_="p-rename")
    db_session.add(proj)
    db_session.commit()

    response = client.patch("/api/projets/p-rename", json={"name": "Nouveau Nom"})
    assert response.status_code == 200
    assert response.json()["name"] == "Nouveau Nom"


# ---------------------------------------------------------------------------
# Suggestions IA (mocké car dépend du LLM)
# ---------------------------------------------------------------------------


def test_suggest_next_steps(client, db_session):
    """POST /api/projets/{id}/suggestions retourne des recommandations IA."""
    proj = _make_projet(id_="p-suggest")
    db_session.add(proj)
    db_session.commit()

    with patch(
        "services.projet_service.ProjetService.suggest_next_steps",
        new_callable=AsyncMock,
        return_value="1. Définir le backlog\n2. Planifier le sprint 1",
    ):
        response = client.post("/api/projets/p-suggest/suggestions")

    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert "sprint" in data["suggestions"]


def test_suggest_next_steps_not_found(client):
    """POST /api/projets/{id}/suggestions retourne 404 si le projet n'existe pas."""
    with patch(
        "services.projet_service.ProjetService.suggest_next_steps",
        new_callable=AsyncMock,
        side_effect=ValueError("Projet introuvable : inexistant-id"),
    ):
        response = client.post("/api/projets/inexistant-id/suggestions")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_projet(client, db_session):
    """DELETE /api/projets/{id} supprime le projet et retourne 204."""
    proj = _make_projet(id_="p-del")
    db_session.add(proj)
    db_session.commit()

    response = client.delete("/api/projets/p-del")
    assert response.status_code == 204

    response = client.get("/api/projets/p-del")
    assert response.status_code == 404


def test_delete_projet_not_found(client):
    """DELETE /api/projets/{id} retourne 404 si le projet n'existe pas."""
    response = client.delete("/api/projets/inexistant-id")
    assert response.status_code == 404
