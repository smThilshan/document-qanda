"""
Question-answering endpoint: retrieves the most relevant stored chunks
for a question, then generates an answer grounded in exactly those
chunks. Retrieval and generation stay as separate service functions (not
merged into this file) so retrieval quality can still be inspected or
tested on its own if needed — this router's job is just wiring the two
together and shaping the HTTP response.
"""

from fastapi import APIRouter, HTTPException

from app.schemas import QueryRequest, QueryResponse
from app.services.generation import GenerationError, generate_answer
from app.services.retrieval import RetrievalError, retrieve_relevant_chunks

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query_chunks(request: QueryRequest) -> QueryResponse:
    # Emptiness/whitespace is already rejected by QueryRequest's
    # validator, and the value it returns is already stripped.
    question = request.question

    try:
        chunks = retrieve_relevant_chunks(question)
    except RetrievalError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    # Either no chunks exist at all, or none cleared MIN_SIMILARITY in
    # retrieve_relevant_chunks — either way, there's nothing worth
    # grounding an answer in. This is a code-enforced guarantee, not the
    # LLM's own judgment call: we skip the LLM entirely rather than send
    # it weak matches and hope it notices.
    if not chunks:
        return QueryResponse(
            question=question,
            answer="No relevant information found in the uploaded document.",
            sources=[],
        )

    try:
        answer = generate_answer(question, chunks)
    except GenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    return QueryResponse(question=question, answer=answer, sources=chunks)
