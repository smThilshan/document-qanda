"""
Centralized configuration loading.

Why this file exists: every other module that needs a secret (API key, DB
credentials) should import from here instead of calling os.getenv() directly.
That gives us ONE place that knows how config is loaded, and ONE place that
fails loudly if something required is missing — instead of, say, the OpenAI
client silently getting `None` as an API key and failing later with a
confusing error deep in a request handler.
"""

import os

from dotenv import load_dotenv

# Reads the .env file in the project root and injects its values into the
# process environment (os.environ). This only affects the current process —
# it does not permanently set your shell's environment variables.
load_dotenv()

REQUIRED_ENV_VARS = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_KEY"]


def _get_required_env_vars() -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []

    for name in REQUIRED_ENV_VARS:
        value = os.getenv(name)
        if not value:
            missing.append(name)
        else:
            values[name] = value

    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): "
            f"{', '.join(missing)}. "
            "Copy .env.example to .env and fill in real values."
        )

    return values


# Fail fast: this runs the moment config.py is first imported (e.g. by
# main.py at startup), not when a route is later called. We want a broken
# config to crash the app on boot with a clear message, not surface as a
# mysterious 500 error the first time someone hits an endpoint.
_env = _get_required_env_vars()

OPENAI_API_KEY = _env["OPENAI_API_KEY"]
SUPABASE_URL = _env["SUPABASE_URL"]
SUPABASE_KEY = _env["SUPABASE_KEY"]

# Not in REQUIRED_ENV_VARS on purpose: unlike the secrets above, this has a
# safe, working default (local dev), so it shouldn't block the app from
# starting if unset. Comma-separated so both a local dev origin and a
# deployed frontend origin can be allowed at once (e.g. while testing a
# deployed backend against a local frontend, or vice versa) without a code
# change — just a different value per environment (Render/Vercel dashboard).
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
