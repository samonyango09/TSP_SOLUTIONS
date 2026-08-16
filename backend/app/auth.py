"""Shared-password gate for the whole app.

This is an internal sales-team tool, not a public product, so a single
app-wide password behind a signed bearer token is the cheapest thing that
still keeps the customer sales data from being open to anyone with the URL.
docs/04-deployment.md calls this out as the first thing to replace with real
per-user accounts (e.g. Supabase Auth) before a wider rollout.

Deliberately a bearer token (frontend stores it and sends
`Authorization: Bearer <token>`), not a cookie. This started as a cookie -
simpler on the frontend, no token storage/interceptor needed - but a real
cross-site deploy (frontend on Vercel, backend on Render, different sites)
exposed why that doesn't hold up: even with the cookie correctly set to
`SameSite=None; Secure` (required for any cross-site cookie at all), modern
browsers' third-party-cookie blocking still silently drops it, since it's
being set by a domain other than the one the user is looking at. Login
would appear to succeed (the response came back 200) while every request
after it failed - confirmed live, not theoretical, while deploying this
project. A bearer token isn't a cookie at all, so no browser cookie policy
applies to it.

If APP_PASSWORD is left unset (local dev default), auth is a no-op - every
request is treated as authenticated - so `uvicorn --reload` works out of the
box without a login step.
"""

from fastapi import Header, HTTPException
from itsdangerous import BadSignature, URLSafeSerializer

from app.config import get_settings


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


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ").strip()


def require_session(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.app_password:
        return  # auth disabled - no password configured
    if not is_valid_session(extract_bearer_token(authorization)):
        raise HTTPException(status_code=401, detail="Not authenticated")


__all__ = ["make_session_token", "is_valid_session", "extract_bearer_token", "require_session"]
