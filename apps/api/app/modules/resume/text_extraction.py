"""
Raw text extraction only. This is deliberately dumb — no skills/experience
structuring here, that's the Phase 5 AI parser's job (parsed_json on the
Resume model). This just gets plain text out of a PDF/DOCX so the file
preview and the future AI call both have something to work with.
"""

import io

from docx import Document
from pypdf import PdfReader


class UnsupportedFileTypeError(Exception):
    pass


def extract_text(*, file_bytes: bytes, content_type: str, filename: str) -> str:
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    if filename.lower().endswith(".docx") or content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }:
        document = Document(io.BytesIO(file_bytes))
        return "\n".join(p.text for p in document.paragraphs).strip()

    raise UnsupportedFileTypeError(
        f"Unsupported resume file type: {content_type or filename}. Use PDF or DOCX."
    )
