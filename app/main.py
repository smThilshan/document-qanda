"""
FastAPI application entry point.

Route logic lives in app/routers/ (HTTP layer only) and business logic in
app/services/ (the actual RAG mechanics); this file just wires routers into
the app. main.py should stay small forever — it's the wiring, not the logic.
"""

from fastapi import FastAPI

from app.routers import documents, query, upload
from app.schemas import HealthResponse

app = FastAPI(title="Document Q&A RAG System")

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents.router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
