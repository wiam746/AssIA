"""Tests des routes Emails — rédaction, analyse, listing."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_draft(
    id_="draft-001",
    subject="Bienvenue !",
    body="Cher client, bienvenue dans notre équipe.",
    tone="neutre",
    mode="redaction",
    created_by="test-user-id-12345",
):
    from models.database import EmailDraft

    return EmailDraft(
        id=id_,
        subject=subject,
        body=body,
        tone=tone,
        mode=mode,
        created_by=created_by,
        created_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Rédaction d'email
# ---------------------------------------------------------------------------


def test_draft_email_success(client):
    """POST /api/emails/draft génère un brouillon et retourne 201."""
    draft = _make_draft()

    with patch(
        "services.email_service.EmailService.draft_email",
        new_callable=AsyncMock,
        return_value=draft,
    ):
        response = client.post(
            "/api/emails/draft",
            json={
                "mode": "redaction",
                "instructions": "Rédiger un email de bienvenue pour un nouveau client.",
                "tone": "neutre",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["subject"] == "Bienvenue !"
    assert data["mode"] == "redaction"


def test_draft_email_wrong_mode(client):
    """POST /api/emails/draft retourne 422 si mode='analyse'."""
    response = client.post(
        "/api/emails/draft",
        json={
            "mode": "analyse",
            "instructions": "Analyser cet email.",
            "tone": "neutre",
        },
    )
    assert response.status_code == 422


def test_draft_email_empty_instructions(client):
    """POST /api/emails/draft retourne 422 si les instructions sont vides."""
    response = client.post(
        "/api/emails/draft",
        json={
            "mode": "redaction",
            "instructions": "",
            "tone": "neutre",
        },
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Analyse d'email
# ---------------------------------------------------------------------------


def test_analyze_email_success(client):
    """POST /api/emails/analyze analyse un email et retourne 201."""
    draft = _make_draft(
        id_="draft-002",
        subject=None,
        body="Synthèse : email commercial agressif.",
        mode="analyse",
    )

    with patch(
        "services.email_service.EmailService.analyze_email",
        new_callable=AsyncMock,
        return_value=draft,
    ):
        response = client.post(
            "/api/emails/analyze",
            json={"email_content": "Cher client, profitez de notre offre exceptionnelle..."},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["mode"] == "analyse"
    assert "Synthèse" in data["body"]


def test_analyze_email_empty_content(client):
    """POST /api/emails/analyze retourne 422 si le contenu est vide."""
    response = client.post("/api/emails/analyze", json={"email_content": ""})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Listing des brouillons
# ---------------------------------------------------------------------------


def test_list_drafts_empty(client):
    """GET /api/emails retourne une liste vide si aucun brouillon."""
    response = client.get("/api/emails")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) == 0


def test_list_drafts_with_data(client, db_session):
    """GET /api/emails retourne les brouillons de l'utilisateur."""
    d1 = _make_draft(id_="d-001", subject="Email 1")
    d2 = _make_draft(id_="d-002", subject="Email 2")
    db_session.add(d1)
    db_session.add(d2)
    db_session.commit()

    response = client.get("/api/emails")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Get by ID
# ---------------------------------------------------------------------------


def test_get_draft_not_found(client):
    """GET /api/emails/{id} retourne 404 si le brouillon n'existe pas."""
    response = client.get("/api/emails/inexistant-id")
    assert response.status_code == 404


def test_get_draft_existing(client, db_session):
    """GET /api/emails/{id} retourne le détail d'un brouillon existant."""
    d = _make_draft(id_="d-get")
    db_session.add(d)
    db_session.commit()

    response = client.get("/api/emails/d-get")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "d-get"
    assert data["subject"] == "Bienvenue !"
