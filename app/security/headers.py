import secrets
from typing import Callable, Dict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse

from app.config import settings
from app.security.exceptions import PayloadTooLargeError


def _header_map(scope) -> Dict[str, str]:
    return {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in scope.get("headers", [])
    }


def _is_https_request(request: Request) -> bool:
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        return forwarded_proto.split(",")[0].strip().lower() == "https"
    return request.url.scheme == "https"


def _wants_json(scope) -> bool:
    path = scope.get("path", "")
    if path.startswith("/api"):
        return True
    headers = _header_map(scope)
    return "application/json" in headers.get("accept", "")


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, enabled: bool) -> None:
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next: Callable):
        if not self.enabled or _is_https_request(request):
            return await call_next(request)
        url = request.url.replace(scheme="https")
        return RedirectResponse(url)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)

    def _build_csp(self, nonce: str) -> str:
        return (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{nonce}'; "
            "script-src-attr 'none'; "
            "style-src 'self' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "frame-ancestors 'none'"
        )

    async def dispatch(self, request: Request, call_next: Callable):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        response = await call_next(request)

        response.headers["Content-Security-Policy"] = self._build_csp(nonce)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        if settings.hsts_enabled and _is_https_request(request):
            response.headers["Strict-Transport-Security"] = (
                f"max-age={settings.hsts_max_age}; includeSubDomains"
            )
        return response


class BodySizeLimitMiddleware:
    def __init__(self, app, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = _header_map(scope)
        content_length = headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > self.max_body_bytes:
                    await self._send_too_large(scope, receive, send)
                    return
            except ValueError:
                pass
        received = 0

        async def receive_wrapper():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                received += len(body)
                if received > self.max_body_bytes:
                    raise PayloadTooLargeError()
            return message

        try:
            await self.app(scope, receive_wrapper, send)
        except PayloadTooLargeError:
            await self._send_too_large(scope, receive, send)

    async def _send_too_large(self, scope, receive, send) -> None:
        if _wants_json(scope):
            response = JSONResponse(
                {"detail": "Payload muito grande."}, status_code=413
            )
        else:
            response = PlainTextResponse("Payload muito grande.", status_code=413)
        await response(scope, receive, send)
