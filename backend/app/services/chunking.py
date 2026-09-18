"""
Splits extracted document text into overlapping chunks for embedding.

WHY TOKEN-BASED, SENTENCE-AWARE CHUNKING (not pure character or pure token):

1. Character-based splitting (e.g. "every 2000 characters") is what a lot
   of quick tutorials do, but it's the wrong unit. OpenAI's embedding model
   has a token limit, not a character limit, and the ratio of characters
   to tokens drifts with punctuation, whitespace, and content (roughly 4
   chars/token in English, but not reliably). Sizing chunks in characters
   means aiming at a proxy for the thing that actually matters.

2. Pure token-based splitting (slice the raw token ID array into fixed-size
   windows) gets the size exactly right, but ignores sentence boundaries
   completely. A chunk can start or end mid-sentence — e.g. "...the
   resulting API response was" — which produces a worse embedding (it's
   embedding a sentence fragment, not a complete thought) and can hand the
   LLM an incomplete clause to reason from at answer time.

3. This module does both: it splits text into sentences first, then
   greedily packs whole sentences into a chunk while counting tokens with
   tiktoken (the real tokenizer OpenAI's models use — not an approximation)
   so we know exactly when we're about to exceed the budget. A chunk never
   ends mid-sentence, but the tradeoff is that chunk sizes become
   *approximate* rather than exact (a chunk might land at 430 tokens or
   790 tokens, not a clean number). That's an intentional tradeoff:
   semantic coherence per chunk matters more for retrieval quality than
   hitting an exact token count.

Overlap works by carrying the trailing sentences of one chunk into the
start of the next, targeting ~15% of the token budget. The reason for
overlap at all: if a fact spans the boundary between two chunks, and only
one of those chunks gets retrieved at query time, overlap increases the
odds that chunk still contains the full fact rather than half of it.

Known limitation, accepted for simplicity: if a single sentence is itself
longer than max_tokens (a huge run-on sentence, or a wall of text with no
punctuation), it becomes its own oversized chunk rather than being split
further. Handling that would mean falling back to a secondary splitter for
just that case — real complexity for a rare edge case, so it's left alone
for now.
"""

import re

import tiktoken

# cl100k_base is the encoding used by OpenAI's text-embedding-3 models.
# Using the real tokenizer means our counts match what the embedding API
# actually sees, rather than an approximation.
_ENCODING = tiktoken.get_encoding("cl100k_base")

# Splits after a sentence-ending punctuation mark followed by whitespace.
# This is a simple heuristic, not a full sentence tokenizer — it will
# occasionally mis-split on abbreviations like "Dr. Smith" — but it avoids
# pulling in a heavy NLP dependency (nltk/spacy) for a problem that mostly
# needs "good enough" sentence boundaries, not perfect ones.
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")

DEFAULT_MAX_TOKENS = 800
DEFAULT_OVERLAP_RATIO = 0.15


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


def _split_into_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [s.strip() for s in _SENTENCE_BOUNDARY.split(normalized) if s.strip()]


def chunk_text(
    text: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    overlap_ratio: float = DEFAULT_OVERLAP_RATIO,
) -> list[str]:
    """
    Split text into overlapping, sentence-respecting chunks of roughly
    max_tokens * (1 - overlap_ratio) to max_tokens tokens each.
    """
    sentences = _split_into_sentences(text)
    if not sentences:
        return []

    sentence_tokens = [(s, count_tokens(s)) for s in sentences]
    overlap_budget = int(max_tokens * overlap_ratio)

    chunks: list[str] = []
    current: list[tuple[str, int]] = []
    current_total = 0

    for sentence, tokens in sentence_tokens:
        if current and current_total + tokens > max_tokens:
            chunks.append(" ".join(s for s, _ in current))

            # Carry trailing sentences into the next chunk as overlap,
            # walking backward until we've collected ~overlap_budget tokens.
            carry: list[tuple[str, int]] = []
            carry_total = 0
            for s, t in reversed(current):
                if carry_total >= overlap_budget:
                    break
                carry.insert(0, (s, t))
                carry_total += t

            current = carry
            current_total = carry_total

        current.append((sentence, tokens))
        current_total += tokens

    if current:
        chunks.append(" ".join(s for s, _ in current))

    return chunks
