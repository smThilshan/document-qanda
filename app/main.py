"""
FastAPI application entry point.

Kept intentionally minimal for Phase 1: just the app instance and a health
check. As we build out real functionality in later phases, route logic will
live in app/routers/ (HTTP layer only) and business logic in app/services/
(the actual RAG mechanics), imported into this file rather than written here.
main.py should stay small forever — it's the wiring, not the logic.
"""

from fastapi import FastAPI

app = FastAPI(title="Document Q&A RAG System")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
