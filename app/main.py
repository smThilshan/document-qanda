"""
FastAPI application entry point.

Route logic lives in app/routers/ (HTTP layer only) and business logic in
app/services/ (the actual RAG mechanics); this file just wires routers into
the app. main.py should stay small forever — it's the wiring, not the logic.
"""

from fastapi import FastAPI

from app.routers import upload

app = FastAPI(title="Document Q&A RAG System")

app.include_router(upload.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
