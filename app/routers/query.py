"""
Question-answering endpoint: retrieves the most relevant stored chunks
for a question, then generates an answer grounded in exactly those
chunks. Retrieval and generation stay as separate service functions (not
merged into this file) so retrieval quality can still be inspected or
tested on its own if needed — this router's job is just wiring the two
together and shaping the HTTP response.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.generation import GenerationError, generate_answer
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
        chunks = retrieve_relevant_chunks(question)
    except RetrievalError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # No stored chunks came back at all (e.g. empty database) — there's
    # nothing to ground an answer in, so skip the LLM call entirely rather
    # than spend a request asking it to say "I don't know."
    if not chunks:
        return {
            "question": question,
            "answer": "I don't know based on the provided document.",
            "sources": [],
        }

    try:
        answer = generate_answer(question, chunks)
    except GenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return {
        "question": question,
        "answer": answer,
        "sources": chunks,
    }
