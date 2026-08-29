"""
Traitement des documents uploades : extraction de texte et decoupage en chunks
avant indexation dans le vector store.

Formats supportes : PDF, DOCX, TXT, Markdown.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger("core.document_processor")


@dataclass
class DocumentChunk:
    """Un fragment de document, pret a etre indexe dans le vector store."""

    chunk_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnsupportedFileTypeError(Exception):
    """Levee quand le type de fichier n'est pas pris en charge par le processor."""


class DocumentProcessor:
    """
    Extrait le texte brut d'un document et le decoupe en chunks de taille
    raisonnable pour l'indexation vectorielle (avec chevauchement pour
    preserver le contexte entre chunks).
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def is_supported(self, file_path: str | Path) -> bool:
        """Indique si l'extension du fichier est prise en charge."""
        return Path(file_path).suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract_text(self, file_path: str | Path) -> str:
        """Extrait le texte brut d'un fichier selon son extension."""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._extract_pdf(path)
        if extension == ".docx":
            return self._extract_docx(path)
        if extension in {".txt", ".md"}:
            return self._extract_plain_text(path)

        raise UnsupportedFileTypeError(
            f"Extension non supportee : '{extension}'. "
            f"Extensions supportees : {sorted(self.SUPPORTED_EXTENSIONS)}"
        )

    @staticmethod
    def _extract_pdf(path: Path) -> str:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages_text)

    @staticmethod
    def _extract_docx(path: Path) -> str:
        import docx

        document = docx.Document(str(path))
        paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    @staticmethod
    def _extract_plain_text(path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="ignore")

    def split_into_chunks(
        self,
        text: str,
        *,
        document_id: str,
        base_metadata: Dict[str, Any] | None = None,
    ) -> List[DocumentChunk]:
        """
        Decoupe un texte en chunks de taille `chunk_size` caracteres, avec un
        chevauchement de `chunk_overlap` caracteres entre chunks consecutifs.
        """
        base_metadata = base_metadata or {}
        cleaned_text = " ".join(text.split())

        if not cleaned_text:
            logger.warning("Texte vide pour le document '%s', aucun chunk genere.", document_id)
            return []

        chunks: List[DocumentChunk] = []
        start = 0
        index = 0
        text_length = len(cleaned_text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_text = cleaned_text[start:end]

            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{index}",
                    text=chunk_text,
                    chunk_index=index,
                    metadata={**base_metadata, "document_id": document_id, "chunk_index": index},
                )
            )

            if end == text_length:
                break

            start = end - self.chunk_overlap
            index += 1

        logger.info("Document '%s' decoupe en %d chunk(s).", document_id, len(chunks))
        return chunks

    def process(
        self,
        file_path: str | Path,
        *,
        document_id: str,
        base_metadata: Dict[str, Any] | None = None,
    ) -> List[DocumentChunk]:
        """Pipeline complet : extraction du texte puis decoupage en chunks."""
        text = self.extract_text(file_path)
        return self.split_into_chunks(text, document_id=document_id, base_metadata=base_metadata)
