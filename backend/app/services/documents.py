"""
Lists uploaded documents and how many chunks each one has.

WHY THIS COUNTS IN PYTHON INSTEAD OF ASKING THE DATABASE TO GROUP/COUNT:

The obvious approach — a SQL "GROUP BY document_name, COUNT(*)" — isn't
reachable through Supabase's normal REST query builder here: this project's
Supabase instance has SQL aggregate functions disabled at the PostgREST
level (db-aggregates-enabled is off), which is actually the sensible
default, since open aggregate queries over REST are a performance/DoS
surface. Rather than add another custom SQL function (like match_chunks)
for something this small, we fetch every row's document_name and count
duplicates here. That's fine at this project's scale (dozens to hundreds
of chunks); it would stop being fine at a scale where pulling one column
for every row becomes expensive — at that point, a proper SQL aggregate
(via an RPC function, same pattern as match_chunks) would be the right
fix.
"""

from app.db.supabase_client import supabase


def list_documents() -> list[dict]:
    response = supabase.table("chunks").select("document_name").execute()

    counts: dict[str, int] = {}
    for row in response.data:
        name = row["document_name"]
        counts[name] = counts.get(name, 0) + 1

    return [
        {"document_name": name, "chunk_count": count}
        for name, count in sorted(counts.items())
    ]
