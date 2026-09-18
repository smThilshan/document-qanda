"""
FastAPI application entry point.

Route logic lives in app/routers/ (HTTP layer only) and business logic in
app/services/ (the actual RAG mechanics); this file just wires routers into
the app. main.py should stay small forever — it's the wiring, not the logic.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import documents, query, upload
from app.schemas import HealthResponse

app = FastAPI(title="Document Q&A RAG System")

# The React dev server (Vite) runs on a different origin (localhost:5173)
# than this API (localhost:8000). Browsers block cross-origin fetch/XHR
# calls by default unless the server explicitly allows the caller's
# origin — this is what makes that allowed, for local development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents.router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
