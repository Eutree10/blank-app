"""Configuration lookup.

Secrets come from `.streamlit/secrets.toml` or the environment. Streamlit
raises when no secrets file exists at all, so every read goes through here —
a missing secret is a normal state, not an error.
"""

from __future__ import annotations

import os


def secret(name: str, default: str | None = None) -> str | None:
    """Read a setting from Streamlit secrets, falling back to the environment."""
    try:
        import streamlit as st

        if name in st.secrets:
            value = st.secrets[name]
            if value not in (None, ""):
                return str(value)
    except Exception:
        # No secrets file, no Streamlit runtime, malformed TOML — all fine.
        pass
    return os.environ.get(name, default)


def strava_credentials() -> tuple[str | None, str | None, str]:
    """(client_id, client_secret, redirect_uri) — ids are None when unset."""
    return (
        secret("STRAVA_CLIENT_ID"),
        secret("STRAVA_CLIENT_SECRET"),
        secret("STRAVA_REDIRECT_URI", "http://localhost:8501") or "http://localhost:8501",
    )
