"""
Retrieval-only endpoint. Given a question, embed it and return the most
similar stored chunks with their similarity scores — no LLM call yet.
Kept as its own step so retrieval quality can be judged directly, before
a generation phase's phrasing could paper over bad retrieval.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.retrieval import RetrievalError, retrieve_relevant_chunks

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


@router.post("/query")
def query_chunks(request: QueryRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    try:
        results = retrieve_relevant_chunks(question)
    except RetrievalError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {"question": question, "results": results}
