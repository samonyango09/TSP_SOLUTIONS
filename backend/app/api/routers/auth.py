from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from app.auth import _COOKIE_NAME, is_valid_session, make_session_token
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


@router.get("/status")
def auth_status(tsp_session: str | None = Cookie(default=None)) -> dict:
    settings = get_settings()
    if not settings.app_password:
        return {"auth_required": False, "authenticated": True}
    return {"auth_required": True, "authenticated": is_valid_session(tsp_session)}


@router.post("/login")
def login(payload: LoginRequest, response: Response) -> dict:
    settings = get_settings()
    if not settings.app_password or payload.password != settings.app_password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    response.set_cookie(
        _COOKIE_NAME,
        make_session_token(),
        httponly=True,
        # The frontend (Vercel) and backend (Render) are on different sites,
        # not just different ports - a "lax" cookie is only sent on same-site
        # requests and top-level navigations, so it silently never reaches
        # the backend on the fetch/XHR calls the frontend actually makes.
        # "none" is required for any cross-site deployment; it in turn
        # requires `secure=True` (HTTPS), which both Vercel and Render give
        # by default, so this is safe to hardcode rather than branch on env.
        samesite="none",
        secure=True,
        max_age=60 * 60 * 24 * 30,
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(_COOKIE_NAME, samesite="none", secure=True)
    return {"authenticated": False}
