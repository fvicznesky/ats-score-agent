"""Pull plain text from uploaded resume or job-description files."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}


class ExtractError(ValueError):
    pass


def extract_text(filename: str, data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ExtractError(
            f"Unsupported file type '{suffix or filename}'. Use .txt, .md, .pdf, or .docx."
        )
    if suffix in {".txt", ".md"}:
        return data.decode("utf-8", errors="replace")
    if suffix == ".pdf":
        return _pdf_text(data)
    return _docx_text(data)


def _pdf_text(data: bytes) -> str:
    reader = PdfReader(BytesIO(data))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    if not text:
        raise ExtractError(
            "Could not read text from that PDF. Export it as text or paste the contents instead."
        )
    return text


def _docx_text(data: bytes) -> str:
    document = Document(BytesIO(data))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            paragraphs.append(" | ".join(cell.text.strip() for cell in row.cells if cell.text.strip()))
    text = "\n".join(paragraphs).strip()
    if not text:
        raise ExtractError("That Word file looks empty.")
    return text
