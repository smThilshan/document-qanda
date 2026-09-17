"""
Shared Pydantic models for request and response bodies.

Centralizing these means every endpoint's shape is declared once, FastAPI
validates *outgoing* responses against them (not just incoming requests),
and /docs renders a precise schema per endpoint instead of a generic
"object" — this is what makes the auto-generated docs actually usable as
real API documentation rather than just a list of paths.

Services (app/services/) intentionally keep returning plain dicts, not
these models — that keeps the business logic layer independent of
FastAPI/Pydantic specifics. Routers are the boundary that converts a
service's plain dict into one of these typed models before it goes out
over HTTP.
"""

from pydantic import BaseModel, field_validator


class HealthResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    filename: str
    total_chunks: int
    chunks_stored: int
    first_chunk_sample: str


class SourceChunk(BaseModel):
    document_name: str
    content: str
    similarity: float


class QueryRequest(BaseModel):
    question: str

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Question must not be empty or whitespace.")
        return v


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceChunk]


class DocumentSummary(BaseModel):
    document_name: str
    chunk_count: int


class DocumentsResponse(BaseModel):
    documents: list[DocumentSummary]
