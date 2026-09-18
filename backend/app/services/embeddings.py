"""
Generates embeddings via OpenAI's text-embedding-3-small model.

WHY BATCH REQUESTS INSTEAD OF ONE CALL PER CHUNK:

OpenAI's embeddings endpoint accepts a *list* of strings in a single
request and returns one embedding per string, in the same order. Calling
it once per chunk means N chunks = N HTTP round trips — for a 200-chunk
document, that's 200 separate network calls, each paying its own latency
overhead, and each counting separately against requests-per-minute rate
limits. Grouping chunks into batches of BATCH_SIZE means the same work
happens in far fewer requests: 200 chunks / 100 per batch = 2 calls.

BATCH_SIZE = 100 is a conservative fixed number, not something dynamically
computed from token counts. At our chunker's upper bound of ~800 tokens
per chunk, 100 chunks is ~80k tokens per request — comfortably under this
endpoint's per-request token ceiling, with a lot of headroom. A fixed
batch size is simpler to reason about than dynamic sizing, and is good
enough for the document sizes this project deals with; a system ingesting
huge documents would eventually want request payload size checks too, but
that's added complexity this project doesn't need yet.

RETRY: a transient failure (rate limit, brief network blip) is retried a
few times with exponential backoff. If a batch still fails after retries,
generate_embeddings_batch raises immediately and stops — it does not
return partial results. See app/routers/upload.py for why that matters:
the router only writes to the database after every chunk has a real
embedding, so a failure here means nothing gets written at all, rather
than half a document silently existing in storage.
"""

import time

from openai import OpenAI, OpenAIError

from app.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100
MAX_RETRIES = 3


class EmbeddingError(Exception):
    """Raised when embedding generation fails even after retries."""


def _embed_batch(texts: list[str]) -> list[list[float]]:
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = _client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in response.data]
        except OpenAIError as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(2**attempt)  # 1s, then 2s

    raise EmbeddingError(
        f"Embedding request failed after {MAX_RETRIES} attempts: {last_error}"
    )


def generate_embedding(text: str) -> list[float]:
    """Embed a single piece of text (e.g. a user's question at query time)."""
    return _embed_batch([text])[0]


def generate_embeddings_batch(chunks: list[str]) -> list[list[float]]:
    """
    Embed many chunks, batching requests to OpenAI. Returns one embedding
    per chunk, in the same order as the input. Raises EmbeddingError on
    the first unrecoverable failure — callers should treat that as "none
    of this succeeded," not "some of this succeeded."
    """
    all_embeddings: list[list[float]] = []

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start : start + BATCH_SIZE]
        all_embeddings.extend(_embed_batch(batch))

    return all_embeddings
