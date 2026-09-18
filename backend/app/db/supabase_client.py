"""
Shared Supabase client.

Why a shared instance instead of creating a new client wherever it's needed:
each `create_client()` call opens its own HTTP connection pool and does setup
work. If every service/router created its own client, we'd waste resources
and have config drift (e.g. one place accidentally using a stale key). By
creating it once here, at import time, every other module just does
`from app.db.supabase_client import supabase` and reuses the same instance —
this is the same "singleton" pattern you'd use for a DB connection pool in
any backend framework.
"""

from supabase import Client, create_client

from app.config import SUPABASE_KEY, SUPABASE_URL

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
