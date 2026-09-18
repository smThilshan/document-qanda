"""
Generates an answer to a question, grounded in retrieved document chunks.

PROMPT STRUCTURE:

The system prompt carries the standing rules — answer only from context,
say so plainly when the answer isn't there — because the system role is
where a model gives the most weight to instructions that should hold for
every request, as opposed to the specific ask in a given turn.

The user message carries the per-request data: the retrieved chunks,
numbered, followed by the question. Numbering them isn't decorative — it
gives the model a concrete way to refer to a specific passage instead of
paraphrasing "the earlier part of the context," and keeps the document
content clearly separated from the question being asked about it.

WHY TEMPERATURE=0:

This is a factual-QA system meant to be grounded strictly in retrieved
text, not a creative-writing task. Temperature controls how much the
model deviates from its highest-probability next token; at 0, it's as
deterministic and conservative as this API allows, which minimizes the
model's tendency to embellish or guess beyond what the context actually
supports, and makes the same question reliably produce the same answer.

WHY "SOURCES" = EVERY RETRIEVED CHUNK, NOT A MODEL SELF-REPORT:

An alternative design would ask the model to name which chunk number(s)
it actually used. That would be the model's own unverified claim about
its own reasoning — models aren't reliably self-aware of which part of a
prompt drove a given output. Instead, this module treats "sources" as
simply everything that was retrieved and handed to the model as context:
a plain, always-true statement of "here is everything the model had
available," rather than trusting a self-report that could be wrong.
"""

from openai import OpenAI, OpenAIError

from app.config import OPENAI_API_KEY

_client = OpenAI(api_key=OPENAI_API_KEY)

GENERATION_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are a document question-answering assistant. Answer the user's question using ONLY the information in the numbered context passages provided.

Rules:
- If the answer is not contained in the context, respond exactly with: "I don't know based on the provided document." Do not guess or use outside knowledge.
- Do not refer to "the context" or "the passages" in your answer — answer naturally, as if you simply know the information.
- Be concise and directly address the question."""


class GenerationError(Exception):
    """Raised when the LLM call fails."""


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    context_block = "\n\n".join(
        f"[{i}] {chunk['content']}" for i, chunk in enumerate(chunks, start=1)
    )
    return f"Context:\n{context_block}\n\nQuestion: {question}"


def generate_answer(question: str, chunks: list[dict]) -> str:
    user_prompt = build_user_prompt(question, chunks)

    try:
        response = _client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
    except OpenAIError as e:
        raise GenerationError(f"Answer generation failed: {e}") from e

    return response.choices[0].message.content
