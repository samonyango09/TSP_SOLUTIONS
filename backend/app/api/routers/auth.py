from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.auth import extract_bearer_token, is_valid_session, make_session_token
from app.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    authenticated: bool
    token: str | None = None


@router.get("/status")
def auth_status(authorization: str | None = Header(default=None)) -> dict:
    settings = get_settings()
    if not settings.app_password:
        return {"auth_required": False, "authenticated": True}
    return {"auth_required": True, "authenticated": is_valid_session(extract_bearer_token(authorization))}


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    settings = get_settings()
    if not settings.app_password or payload.password != settings.app_password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return LoginResponse(authenticated=True, token=make_session_token())
