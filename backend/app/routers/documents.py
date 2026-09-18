"""
Lets you check what document is currently stored without needing to open
Supabase directly. Under the current single-document-at-a-time constraint
(see app/routers/upload.py), this will show at most one document — it's
written generically so it keeps working correctly if multi-document
support is added later.
"""

from fastapi import APIRouter

from app.schemas import DocumentsResponse
from app.services.documents import list_documents

router = APIRouter()


@router.get("/documents", response_model=DocumentsResponse)
def get_documents() -> DocumentsResponse:
    return DocumentsResponse(documents=list_documents())
