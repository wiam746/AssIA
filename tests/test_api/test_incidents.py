"""Tests des routes Incidents — CRUD complet."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_incident(
    id_="inc-001",
    title="Panne base de données",
    severity="majeur",
    status="ouvert",
    reported_by="test-user-id-12345",
):
    from models.database import Incident

    return Incident(
        id=id_,
        title=title,
        description="La base de données ne répond plus.",
        severity=severity,
        status=status,
        analysis="Analyse IA : surcharge probable.",
        reported_by=reported_by,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Listing
# ---------------------------------------------------------------------------


def test_list_incidents_empty(client):
    """GET /api/incidents retourne une liste vide initialement."""
    response = client.get("/api/incidents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_incidents_with_data(client, db_session):
    """GET /api/incidents retourne tous les incidents présents en base."""
    inc = _make_incident()
    db_session.add(inc)
    db_session.commit()

    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Panne base de données"
    assert data[0]["severity"] == "majeur"


def test_list_incidents_filter_by_status(client, db_session):
    """GET /api/incidents?status=resolu ne retourne que les incidents résolus."""
    ouvert = _make_incident(id_="i-open", title="Incident ouvert", status="ouvert")
    resolu = _make_incident(id_="i-done", title="Incident résolu", status="resolu")
    db_session.add(ouvert)
    db_session.add(resolu)
    db_session.commit()

    response = client.get("/api/incidents?status=resolu")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "resolu"


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_incident_not_found(client):
    """GET /api/incidents/{id} retourne 404 si l'incident n'existe pas."""
    response = client.get("/api/incidents/inexistant-id")
    assert response.status_code == 404


def test_get_incident_existing(client, db_session):
    """GET /api/incidents/{id} retourne le détail d'un incident existant."""
    inc = _make_incident(id_="i-detail")
    db_session.add(inc)
    db_session.commit()

    response = client.get("/api/incidents/i-detail")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "i-detail"
    assert data["severity"] == "majeur"


# ---------------------------------------------------------------------------
# Create (mocké car dépend du LLM)
# ---------------------------------------------------------------------------


def test_create_incident(client):
    """POST /api/incidents crée un incident et retourne 201."""
    incident = _make_incident()

    with patch(
        "services.incident_service.IncidentService.create_incident",
        new_callable=AsyncMock,
        return_value=incident,
    ), patch(
        "services.incident_service.IncidentService.list_incident_documents",
        return_value=[],
    ):
        response = client.post(
            "/api/incidents",
            json={
                "title": "Panne base de données",
                "description": "La base ne répond plus.",
                "severity": "majeur",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Panne base de données"
    assert data["status"] == "ouvert"


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


def test_update_incident_not_found(client):
    """PATCH /api/incidents/{id} retourne 404 si l'incident n'existe pas."""
    response = client.patch(
        "/api/incidents/inexistant-id",
        json={"status": "resolu"},
    )
    assert response.status_code == 404


def test_update_incident_status(client, db_session):
    """PATCH /api/incidents/{id} met à jour le statut d'un incident."""
    inc = _make_incident(id_="i-upd")
    db_session.add(inc)
    db_session.commit()

    response = client.patch(
        "/api/incidents/i-upd",
        json={"status": "en_cours", "resolution": "Investigation en cours."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "en_cours"


def test_resolve_incident(client, db_session):
    """PATCH /api/incidents/{id} marque un incident comme résolu."""
    inc = _make_incident(id_="i-resolu")
    db_session.add(inc)
    db_session.commit()

    response = client.patch(
        "/api/incidents/i-resolu",
        json={"status": "resolu", "resolution": "Redémarrage du serveur."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "resolu"


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def test_delete_incident(client, db_session):
    """DELETE /api/incidents/{id} supprime l'incident et retourne 204."""
    inc = _make_incident(id_="i-del")
    db_session.add(inc)
    db_session.commit()

    response = client.delete("/api/incidents/i-del")
    assert response.status_code == 204

    response = client.get("/api/incidents/i-del")
    assert response.status_code == 404


def test_delete_incident_not_found(client):
    """DELETE /api/incidents/{id} retourne 404 si l'incident n'existe pas."""
    response = client.delete("/api/incidents/inexistant-id")
    assert response.status_code == 404
