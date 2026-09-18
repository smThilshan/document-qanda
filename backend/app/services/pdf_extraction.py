"""
PDF text extraction, kept separate from the router.

The router's job is HTTP concerns only (status codes, response shape).
Extraction logic lives here so it can be reasoned about and tested on its
own — and so Phase 4+ can reuse it without dragging in FastAPI request
objects.
"""

import io

from pypdf import PdfReader


class PDFExtractionError(Exception):
    """Raised when a PDF can't be parsed or has no extractable text."""


def extract_text_from_pdf(file_bytes: bytes) -> str:
    # pypdf can raise several different exception types for malformed
    # input (corrupt structure, wrong file signature, etc.) — we don't
    # know in advance which one a bad upload will trigger, so this catches
    # broadly and wraps it in one clear, predictable error type for the
    # router to handle. This is a trust boundary (arbitrary user-uploaded
    # bytes), which is exactly where a broad except is appropriate.
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:
        raise PDFExtractionError(f"Could not read PDF: {e}") from e

    full_text = "\n".join(pages_text).strip()

    if not full_text:
        raise PDFExtractionError(
            "No extractable text found in this PDF "
            "(it may be empty, or a scanned image with no text layer)."
        )

    return full_text
