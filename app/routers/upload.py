"""
Document upload endpoint.

Phase 2 scope: accept a PDF, extract its text, split it into chunks, and
report back what *would* be stored — no database writes yet (that's the
next phase). The endpoint itself stays thin: it validates the HTTP-level
concerns (was a file sent, is it a PDF) and delegates the real work to
app/services/, which is what keeps main.py-adjacent files small as the
project grows.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.chunking import chunk_text
from app.services.pdf_extraction import PDFExtractionError, extract_text_from_pdf

router = APIRouter()


@router.post("/upload")
async def upload_document(file: UploadFile | None = File(None)):
    if file is None:
        raise HTTPException(status_code=400, detail="No file provided.")

    filename = file.filename or ""
    # Content-Type headers are client-supplied and not always reliable
    # (some clients send application/octet-stream for any binary file), so
    # we treat the filename extension as a fallback signal rather than the
    # single source of truth. The real validation is whether pypdf can
    # actually parse the bytes, which happens below.
    looks_like_pdf = (
        file.content_type == "application/pdf" or filename.lower().endswith(".pdf")
    )
    if not looks_like_pdf:
        raise HTTPException(status_code=400, detail="File must be a PDF.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_pdf(file_bytes)
    except PDFExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    chunks = chunk_text(text)

    return {
        "filename": filename,
        "total_chunks": len(chunks),
        "first_chunk_sample": chunks[0] if chunks else None,
    }
