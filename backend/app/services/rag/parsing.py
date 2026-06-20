"""Extract plain text from uploaded document bytes.

Each supported type has its own extractor; `extract_text` dispatches by file
extension and normalizes every failure to `DocumentParseError` so the worker
can mark a document `failed` with a clear reason rather than crashing.
"""

from __future__ import annotations

import io
import os

import docx
from pypdf import PdfReader


class DocumentParseError(Exception):
    """Raised when a document's bytes cannot be turned into usable text."""


def _extract_text_file(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _extract_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    # Blank line between pages so the chunker sees page-sized paragraph blocks.
    return "\n\n".join(page for page in pages if page)


def _extract_docx(data: bytes) -> str:
    document = docx.Document(io.BytesIO(data))
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


_EXTRACTORS = {
    ".txt": _extract_text_file,
    ".md": _extract_text_file,
    ".pdf": _extract_pdf,
    ".docx": _extract_docx,
}


def extract_text(data: bytes, *, filename: str) -> str:
    extension = os.path.splitext(filename)[1].lower()
    extractor = _EXTRACTORS.get(extension)
    if extractor is None:
        raise DocumentParseError(f"Unsupported document type: {extension or '(none)'}")

    try:
        text = extractor(data)
    except Exception as exc:  # normalize any parser-internal error
        raise DocumentParseError(f"Failed to parse {extension} document") from exc

    if not text.strip():
        raise DocumentParseError(f"No extractable text in {extension} document")
    return text
