"""
Retrieval: given a question, find the most semantically similar chunks
already stored in Supabase. No generation here — that's a later phase.
This is deliberately isolated so retrieval quality can be checked on its
own before an LLM's phrasing has a chance to mask a bad retrieval.

WHY THE QUESTION MUST BE EMBEDDED WITH THE SAME MODEL AS THE CHUNKS:

An embedding model defines its own vector space — where a given piece of
text lands is meaningful only relative to that same model's other
outputs. Two different models (or even two versions of the same model)
don't share a coordinate system: a value on one axis from
text-embedding-3-small has no defined relationship to the "same" axis
from a different model. If the question were embedded with a different
model than the one used for the stored chunks, pgvector would still
happily compute a distance between the two vectors — but that number
would be meaningless, since the two vectors don't live in a comparable
space. So this reuses generate_embedding() from app/services/embeddings.py
— the exact same function, same model constant — rather than
re-specifying the model name here, precisely so the two can never drift
apart.

WHY COSINE DISTANCE:

pgvector offers three distance operators: L2 (<->), inner product (<#>),
and cosine (<=>). OpenAI's documentation recommends cosine similarity for
its embedding models: it measures the angle between two vectors rather
than their magnitude, which fits embeddings, where meaning is encoded in
direction rather than length. (OpenAI's embeddings are close to
unit-length already, so cosine and dot-product would rank results nearly
identically here — but cosine is the explicit, conventional choice and
doesn't depend on that normalization holding exactly.)

pgvector's <=> operator returns *distance* (0 = identical, larger = less
alike) — the opposite direction of "similarity". The match_chunks SQL
function (see setup instructions) converts this with `1 - distance` so
the API returns a score where higher means more relevant, which reads
more naturally.

WHY A HARD SIMILARITY THRESHOLD (MIN_SIMILARITY):

match_chunks always returns its top N rows, even if none of them are
actually relevant — pgvector doesn't know what "relevant" means, only
"closest of what exists." Without a cutoff, an off-topic question still
gets handed 5 chunks of context, and we're relying entirely on the LLM's
system prompt to notice they're irrelevant and say so. That worked in
testing, but it's the model's judgment call, not a guarantee.

MIN_SIMILARITY = 0.25 was set empirically, not guessed: against this
project's real test data, genuinely relevant matches scored 0.36-0.41,
and a deliberately unrelated question scored 0.07-0.11 — a wide, clean
gap. 0.25 sits comfortably in that gap. This is a heuristic tied to
OpenAI's text-embedding-3-small on this kind of document; a different
embedding model or very different content (e.g. short, keyword-sparse
text) could shift where relevant/irrelevant scores actually fall, so this
number is a starting point to revisit if retrieval quality looks off on
a different corpus, not a universal constant.
"""

from app.db.supabase_client import supabase
from app.services.embeddings import EmbeddingError, generate_embedding

DEFAULT_MATCH_COUNT = 5
MIN_SIMILARITY = 0.25


class RetrievalError(Exception):
    """Raised when embedding the question or searching Supabase fails."""


def retrieve_relevant_chunks(
    question: str, match_count: int = DEFAULT_MATCH_COUNT
) -> list[dict]:
    """
    Returns chunks similar enough to be worth answering from. May return
    fewer than match_count (including zero) if nothing clears
    MIN_SIMILARITY — that's the caller's signal to treat this as "nothing
    relevant found" rather than force an answer from weak matches.
    """
    try:
        query_embedding = generate_embedding(question)
    except EmbeddingError as e:
        raise RetrievalError(f"Failed to embed question: {e}") from e

    try:
        response = supabase.rpc(
            "match_chunks",
            {"query_embedding": query_embedding, "match_count": match_count},
        ).execute()
    except Exception as e:
        raise RetrievalError(f"Similarity search failed: {e}") from e

    return [row for row in response.data if row["similarity"] >= MIN_SIMILARITY]
