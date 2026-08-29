"""Tests des routes Réunions — CRUD complet."""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_reunion(
    id_="reunion-001",
    title="Synchro Hebdo",
    status="brouillon",
    created_by="test-user-id-12345",
):
    from models.database import Reunion

    r = Reunion(
        id=id_,
        title=title,
        raw_content="Notes brutes.",
        summary="Résumé IA.",
        decisions="Décisions.",
        actions="Actions.",
        objet="Synchro",
        prochaine_reunion="Mardi 10h",
        status=status,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )
    return r


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


def test_list_reunions_empty(client):
    """GET /api/reunions retourne une liste vide initialement."""
    response = client.get("/api/reunions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_reunions_with_data(client, db_session):
    """GET /api/reunions retourne les réunions de l'utilisateur."""
    from models.database import Reunion

    r = Reunion(
        id="r-001",
        title="Réunion test",
        raw_content="Contenu.",
        summary="Résumé.",
        decisions="Aucune.",
        actions="Aucune.",
        objet="Objet",
        prochaine_reunion="Non précisé",
        status="brouillon",
        created_by="test-user-id-12345",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(r)
    db_session.commit()

    response = client.get("/api/reunions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Réunion test"


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_reunion_not_found(client):
    """GET /api/reunions/{id} retourne 404 si la réunion n'existe pas."""
    response = client.get("/api/reunions/inexistant-id")
    assert response.status_code == 404


def test_get_reunion_existing(client, db_session):
    """GET /api/reunions/{id} retourne le détail d'une réunion existante."""
    from models.database import Reunion

    r = Reunion(
        id="r-002",
        title="Réunion Q4",
        raw_content="Notes.",
        summary="Résumé.",
        decisions="Décisions.",
        actions="Actions.",
        objet="Planning Q4",
        prochaine_reunion="Mois prochain",
        status="brouillon",
        created_by="test-user-id-12345",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(r)
    db_session.commit()

    response = client.get("/api/reunions/r-002")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "r-002"
    assert data["title"] == "Réunion Q4"


# ---------------------------------------------------------------------------
# Create (mocké car dépend du LLM)
# ---------------------------------------------------------------------------


def test_create_reunion(client):
    """POST /api/reunions crée une réunion et retourne 201."""
    reunion = _make_reunion()

    with patch(
        "services.reunion_service.ReunionService.create_reunion",
        new_callable=AsyncMock,
        return_value=reunion,
    ):
        response = client.post(
            "/api/reunions",
            json={
                "title": "Synchro Hebdo",
                "raw_content": "Notes brutes de la réunion.",
                "participants": "Alice, Bob",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Synchro Hebdo"
    assert data["status"] == "brouillon"


# ---------------------------------------------------------------------------
# Update / Validation humaine
# ---------------------------------------------------------------------------


def test_update_reunion_not_found(client):
    """PATCH /api/reunions/{id} retourne 404 si la réunion n'existe pas."""
    response = client.patch(
        "/api/reunions/inexistant-id",
        json={"status": "valide"},
    )
    assert response.status_code == 404


def test_update_reunion_status(client, db_session):
    """PATCH /api/reunions/{id} valide une réunion (brouillon → valide)."""
    from models.database import Reunion

    r = Reunion(
        id="r-003",
        title="Réunion Bilan",
        raw_content="Notes.",
        summary="Résumé.",
        decisions="Décisions.",
        actions="Actions.",
        objet="Bilan",
        prochaine_reunion="N/A",
        status="brouillon",
        created_by="test-user-id-12345",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(r)
    db_session.commit()

    response = client.patch("/api/reunions/r-003", json={"status": "valide"})
    assert response.status_code == 200
    assert response.json()["status"] == "valide"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_reunion(client, db_session):
    """DELETE /api/reunions/{id} supprime la réunion et retourne 204."""
    from models.database import Reunion

    r = Reunion(
        id="r-del",
        title="À supprimer",
        raw_content="Notes.",
        summary="Résumé.",
        decisions="Aucune.",
        actions="Aucune.",
        objet="Objet",
        prochaine_reunion="N/A",
        status="brouillon",
        created_by="test-user-id-12345",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(r)
    db_session.commit()

    response = client.delete("/api/reunions/r-del")
    assert response.status_code == 204

    # Vérifie que la ressource est bien supprimée
    response = client.get("/api/reunions/r-del")
    assert response.status_code == 404


def test_delete_reunion_not_found(client):
    """DELETE /api/reunions/{id} retourne 404 si la réunion n'existe pas."""
    response = client.delete("/api/reunions/inexistant-id")
    assert response.status_code == 404
