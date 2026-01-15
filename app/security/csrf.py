import secrets
from typing import Optional

from fastapi import Request, Response

from app.config import settings
from app.security.exceptions import CSRFError


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def get_or_create_csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token") if request.session else None
    if not token:
        token = _generate_token()
        if request.session is not None:
            request.session["csrf_token"] = token
    return token


def set_csrf_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        settings.csrf_cookie_name,
        token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite=settings.csrf_cookie_samesite,
        path="/",
    )


def validate_csrf(request: Request, token: Optional[str] = None) -> None:
    session_token = request.session.get("csrf_token") if request.session else None
    candidate = (
        token
        or request.headers.get("x-csrf-token")
        or request.headers.get("x-xsrf-token")
    )
    if not session_token:
        raise CSRFError("Sessao CSRF ausente.")
    if not candidate:
        raise CSRFError("Token CSRF ausente.")
    if not secrets.compare_digest(session_token, candidate):
        raise CSRFError("Token CSRF invalido.")
