"""Tests du service DocumentService — validation, listing, suppression."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from pathlib import Path

from config.settings import settings
from services.document_service import DocumentService, DocumentValidationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    db = MagicMock()
    query_mock = MagicMock()
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = []
    query_mock.first.return_value = None
    db.query.return_value = query_mock
    return db


@pytest.fixture
def mock_rag():
    rag = MagicMock()
    rag.index_document = AsyncMock(return_value=5)
    rag.remove_document = AsyncMock()
    return rag


@pytest.fixture
def service(mock_db, mock_rag, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    svc = DocumentService(db=mock_db, rag_service=mock_rag)
    svc.upload_dir = tmp_path
    return svc


# ---------------------------------------------------------------------------
# Validation de l'upload
# ---------------------------------------------------------------------------


class TestDocumentValidation:
    """Tests de la méthode _validate_upload."""

    def test_valid_txt(self, service):
        """Un fichier .txt valide ne lève pas d'exception."""
        service._validate_upload("rapport.txt", 1024)  # 1 Ko → OK

    def test_valid_pdf(self, service):
        """Un fichier .pdf valide ne lève pas d'exception."""
        service._validate_upload("compte_rendu.pdf", 512 * 1024)  # 512 Ko → OK

    def test_valid_docx(self, service):
        """Un fichier .docx valide ne lève pas d'exception."""
        service._validate_upload("synthese.docx", 200 * 1024)

    def test_valid_md(self, service):
        """Un fichier .md valide ne lève pas d'exception."""
        service._validate_upload("notes.md", 4096)

    def test_invalid_extension(self, service):
        """Un fichier .exe lève DocumentValidationError."""
        with pytest.raises(DocumentValidationError, match="non autorisee"):
            service._validate_upload("virus.exe", 1024)

    def test_invalid_html_extension(self, service):
        """Un fichier .html lève DocumentValidationError."""
        with pytest.raises(DocumentValidationError):
            service._validate_upload("page.html", 1024)

    def test_file_too_large(self, service):
        """Un fichier dépassant la taille limite lève DocumentValidationError."""
        oversized = (50 + 1) * 1024 * 1024  # 51 Mo si limite à 50 Mo
        with pytest.raises(DocumentValidationError, match="volumineux"):
            service._validate_upload("gros_fichier.pdf", oversized)


# ---------------------------------------------------------------------------
# save_upload
# ---------------------------------------------------------------------------


class TestSaveUpload:
    """Tests de la méthode save_upload."""

    def test_save_upload_creates_file(self, service, tmp_path):
        """save_upload écrit le fichier sur le disque et retourne un Document."""
        content = b"Contenu du rapport de reunion."
        doc = service.save_upload(
            file_bytes=content,
            original_filename="rapport.txt",
            content_type="text/plain",
            uploaded_by="user-1",
        )
        # Vérifie que le fichier existe bien sur le disque
        assert Path(doc.file_path).exists()
        assert doc.status == "pending"
        assert doc.original_filename == "rapport.txt"
        assert doc.file_size == len(content)

    def test_save_upload_rejects_invalid_extension(self, service):
        """save_upload refuse les extensions non autorisées."""
        with pytest.raises(DocumentValidationError):
            service.save_upload(
                file_bytes=b"<html></html>",
                original_filename="page.html",
                content_type="text/html",
            )

    def test_save_upload_calls_db_commit(self, service, mock_db):
        """save_upload persiste le document en base de données."""
        service.save_upload(
            file_bytes=b"Contenu test",
            original_filename="test.txt",
            content_type="text/plain",
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ---------------------------------------------------------------------------
# _process_document (indexation)
# ---------------------------------------------------------------------------


class TestProcessDocument:
    """Tests de la méthode interne _process_document."""

    @pytest.mark.asyncio
    async def test_process_sets_status_indexed(self, service, tmp_path):
        """_process_document met le statut à 'indexed' après succès."""
        from models.database import Document

        doc_file = tmp_path / "test.txt"
        doc_file.write_bytes(b"Contenu a indexer.")

        doc = MagicMock(spec=Document)
        doc.id = "doc-123"
        doc.file_path = str(doc_file)
        doc.original_filename = "test.txt"
        doc.content_type = "text/plain"

        await service._process_document(doc)

        assert doc.status == "indexed"
        service.rag_service.index_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_sets_status_error_on_failure(self, service, mock_rag, tmp_path):
        """_process_document met le statut à 'error' si l'indexation échoue."""
        from models.database import Document

        doc_file = tmp_path / "fail.txt"
        doc_file.write_bytes(b"Contenu.")

        mock_rag.index_document = AsyncMock(side_effect=RuntimeError("ChromaDB indisponible"))

        doc = MagicMock(spec=Document)
        doc.id = "doc-fail"
        doc.file_path = str(doc_file)
        doc.original_filename = "fail.txt"
        doc.content_type = "text/plain"

        await service._process_document(doc)

        assert doc.status == "error"
        assert "ChromaDB" in doc.error_message


# ---------------------------------------------------------------------------
# list_documents
# ---------------------------------------------------------------------------


class TestListDocuments:
    """Tests de la méthode list_documents."""

    def test_list_all(self, service, mock_db):
        """list_documents sans filtre retourne tous les documents."""
        from models.database import Document
        mock_doc = MagicMock(spec=Document)
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_doc]

        results = service.list_documents()
        assert len(results) == 1

    def test_list_filtered_by_user(self, service, mock_db):
        """list_documents filtre par uploaded_by."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        results = service.list_documents(uploaded_by="user-xyz")
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# delete_document
# ---------------------------------------------------------------------------


class TestDeleteDocument:
    """Tests de la méthode delete_document."""

    @pytest.mark.asyncio
    async def test_delete_existing(self, service, mock_db, tmp_path):
        """delete_document supprime le document de la DB et du disque."""
        from models.database import Document

        doc_file = tmp_path / "to_delete.txt"
        doc_file.write_bytes(b"Contenu.")

        mock_doc = MagicMock(spec=Document)
        mock_doc.id = "doc-del"
        mock_doc.file_path = str(doc_file)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_doc

        result = await service.delete_document("doc-del")

        assert result is True
        assert not doc_file.exists()
        mock_db.delete.assert_called_once_with(mock_doc)

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, service, mock_db):
        """delete_document retourne False si le document n'existe pas."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.delete_document("doc-inexistant")
        assert result is False
