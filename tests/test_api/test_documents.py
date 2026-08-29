"""Tests des routes Documents — upload, list, delete."""

import io
from unittest.mock import AsyncMock, patch


def test_list_documents_empty(client):
    """GET /api/documents retourne une liste vide initialement."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_upload_document_txt(client):
    """POST /api/documents/upload indexe un fichier TXT avec succès."""
    file_content = "Contenu de test pour le document texte. Réunion du 15 janvier.".encode("utf-8")
    file = io.BytesIO(file_content)

    with patch(
        "services.document_service.DocumentService.save_upload"
    ) as mock_upload:
        from models.database import Document
        from datetime import datetime, timezone

        mock_doc = Document(
            id="doc-test-123",
            filename="stored_test.txt",
            original_filename="test.txt",
            file_path="./data/uploads/stored_test.txt",
            file_size=len(file_content),
            content_type="text/plain",
            status="pending",
            uploaded_by="test-user-id-12345",
            created_at=datetime.now(timezone.utc),
        )
        mock_upload.return_value = mock_doc

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", file, "text/plain")},
        )

    assert response.status_code == 201
    data = response.json()
    assert "document" in data
    assert data["document"]["original_filename"] == "test.txt"


def test_upload_document_invalid_extension(client):
    """POST /api/documents/upload refuse les extensions non autorisées."""
    file_content = b"<html><body>Fichier HTML</body></html>"
    file = io.BytesIO(file_content)

    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.html", file, "text/html")},
    )
    # Doit retourner 400 ou 422 selon la validation
    assert response.status_code in (400, 422)


def test_delete_document(client):
    """DELETE /api/documents/{id} supprime le document et retourne 204."""
    with patch(
        "api.routes.documents.DocumentService.delete_document",
        new_callable=AsyncMock,
        return_value=True,
    ):
        response = client.delete("/api/documents/doc-test-123")

    assert response.status_code == 204


def test_delete_nonexistent_document(client):
    """DELETE /api/documents/{id} retourne 404 si le document n'existe pas."""
    with patch(
        "api.routes.documents.DocumentService.delete_document",
        new_callable=AsyncMock,
        return_value=False,
    ):
        response = client.delete("/api/documents/nonexistent-doc-id")

    assert response.status_code == 404
