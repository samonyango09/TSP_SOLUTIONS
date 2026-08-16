"""Shared-password gate for the whole app.

This is an internal sales-team tool, not a public product, so a single
app-wide password behind a signed session cookie is the cheapest thing that
still keeps the customer sales data from being open to anyone with the URL.
docs/04-deployment.md calls this out as the first thing to replace with real
per-user accounts (e.g. Supabase Auth) before a wider rollout.

If APP_PASSWORD is left unset (local dev default), auth is a no-op - every
request is treated as authenticated - so `uvicorn --reload` works out of the
box without a login step.
"""

from fastapi import Cookie, HTTPException
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import get_settings

_COOKIE_NAME = "tsp_session"


def _serializer() -> URLSafeSerializer:
    return URLSafeSerializer(get_settings().session_secret, salt="tsp-auth")


def make_session_token() -> str:
    return _serializer().dumps({"authenticated": True})


def is_valid_session(token: str | None) -> bool:
    if token is None:
        return False
    try:
        data = _serializer().loads(token)
    except BadSignature:
        return False
    return bool(data.get("authenticated"))


def require_session(tsp_session: str | None = Cookie(default=None)) -> None:
    settings = get_settings()
    if not settings.app_password:
        return  # auth disabled - no password configured
    if not is_valid_session(tsp_session):
        raise HTTPException(status_code=401, detail="Not authenticated")


__all__ = ["_COOKIE_NAME", "make_session_token", "is_valid_session", "require_session"]
