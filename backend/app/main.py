"""
FastAPI application entry point.

Route logic lives in app/routers/ (HTTP layer only) and business logic in
app/services/ (the actual RAG mechanics); this file just wires routers into
the app. main.py should stay small forever — it's the wiring, not the logic.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ALLOWED_ORIGINS
from app.routers import documents, query, upload
from app.schemas import HealthResponse

app = FastAPI(title="Document Q&A RAG System")

# Which origins may call this API from a browser is environment-specific
# (localhost:5173 in dev, a real Vercel URL in production) — read from
# ALLOWED_ORIGINS via config.py rather than hardcoded here, so switching
# environments is a dashboard env var change, not a code change/redeploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(query.router)
app.include_router(documents.router)


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
