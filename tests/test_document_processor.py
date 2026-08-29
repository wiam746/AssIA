"""Tests du DocumentProcessor — extraction de texte et découpage en chunks."""

import tempfile
import os
import pytest


class TestDocumentProcessor:
    """Tests de l'extraction de texte et du chunking par format de fichier."""

    def test_process_txt_file(self):
        """Doit extraire le texte d'un fichier TXT et retourner des chunks."""
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Ceci est un document de test.\n" * 20)
            tmp_path = f.name

        try:
            chunks = processor.process(tmp_path, document_id="test-doc-txt")
            assert len(chunks) > 0
            for chunk in chunks:
                assert hasattr(chunk, "chunk_id")
                assert hasattr(chunk, "text")
                assert hasattr(chunk, "metadata")
                assert "document_id" in chunk.metadata
                assert chunk.text.strip() != ""
        finally:
            os.unlink(tmp_path)

    def test_process_md_file(self):
        """Doit traiter un fichier Markdown et retourner des chunks."""
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        markdown_content = (
            "# Titre principal\n\n"
            "## Section 1\n\n"
            "Contenu de la section 1. " * 10 + "\n\n"
            "## Section 2\n\n"
            "Contenu de la section 2. " * 10 + "\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(markdown_content)
            tmp_path = f.name

        try:
            chunks = processor.process(tmp_path, document_id="test-doc-md")
            assert len(chunks) > 0
        finally:
            os.unlink(tmp_path)

    def test_chunk_ids_are_unique(self):
        """Chaque chunk doit avoir un identifiant unique."""
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()
        content = "Paragraphe de contenu numérique. " * 50

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp_path = f.name

        try:
            chunks = processor.process(tmp_path, document_id="test-unique")
            ids = [chunk.chunk_id for chunk in chunks]
            assert len(ids) == len(set(ids)), "Les chunk_id ne sont pas uniques"
        finally:
            os.unlink(tmp_path)

    def test_metadata_contains_document_id(self):
        """Les métadonnées de chaque chunk doivent contenir le document_id."""
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Contenu document. " * 10)
            tmp_path = f.name

        try:
            chunks = processor.process(tmp_path, document_id="my-doc-id")
            for chunk in chunks:
                assert chunk.metadata.get("document_id") == "my-doc-id"
        finally:
            os.unlink(tmp_path)

    def test_empty_file_returns_empty_list(self):
        """Un fichier vide doit retourner une liste vide de chunks."""
        from core.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("")
            tmp_path = f.name

        try:
            chunks = processor.process(tmp_path, document_id="empty-doc")
            assert chunks == []
        finally:
            os.unlink(tmp_path)
