"""
Document upload endpoint.

Accepts a PDF, extracts its text, chunks it, embeds every chunk, and
stores the results in Supabase. The endpoint stays thin — HTTP-level
validation only — with extraction, chunking, embedding, and storage each
delegated to app/services/ or app/db/.

ATOMICITY: embeddings for every chunk are generated FIRST, entirely in
memory, before a single row is written to the database. Only once all of
them succeed do we do one insert() call with every row. This is what
keeps a failure partway through from leaving a "half a document" of
chunks silently sitting in the chunks table — either every chunk for this
upload lands in the database, or (if anything fails) none do.
"""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.supabase_client import supabase
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingError, generate_embeddings_batch
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
    if not chunks:
        raise HTTPException(
            status_code=400, detail="No chunks could be produced from this PDF."
        )

    # Generate every embedding before touching the database — see module
    # docstring for why. If this raises, nothing has been written yet.
    try:
        embeddings = generate_embeddings_batch(chunks)
    except EmbeddingError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Embedding generation failed; no data was stored. {e}",
        ) from e

    rows = [
        {"document_name": filename, "content": chunk, "embedding": embedding}
        for chunk, embedding in zip(chunks, embeddings)
    ]

    # A single insert() call with the full row list is one SQL INSERT
    # statement — Postgres runs it as one atomic transaction, so this
    # either stores every chunk for this document, or (if it raises)
    # stores none of them.
    try:
        supabase.table("chunks").insert(rows).execute()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to store chunks in the database: {e}",
        ) from e

    return {
        "filename": filename,
        "total_chunks": len(chunks),
        "chunks_stored": len(rows),
        "first_chunk_sample": chunks[0],
    }
