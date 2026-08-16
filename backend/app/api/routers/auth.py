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
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie(_COOKIE_NAME)
    return {"authenticated": False}
