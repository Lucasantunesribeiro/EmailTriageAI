import logging
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    detail = "Requisicao invalida."

    def __init__(
        self, detail: Optional[str] = None, status_code: Optional[int] = None
    ) -> None:
        if detail:
            self.detail = detail
        if status_code:
            self.status_code = status_code
        super().__init__(self.detail)


class CSRFError(AppError):
    status_code = 403
    detail = "Token CSRF invalido."


class RateLimitError(AppError):
    status_code = 429
    detail = "Muitas requisicoes."


class UploadValidationError(AppError):
    status_code = 400
    detail = "Upload invalido."


class PayloadTooLargeError(AppError):
    status_code = 413
    detail = "Payload muito grande."


def is_api_request(request: Request) -> bool:
    if request.url.path.startswith("/api"):
        return True
    accept = request.headers.get("accept", "")
    return "application/json" in accept


def _error_response(request: Request, status_code: int, detail: str):
    if is_api_request(request):
        return JSONResponse({"detail": detail}, status_code=status_code)
    return PlainTextResponse(detail, status_code=status_code)


def add_exception_handlers(app) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return _error_response(request, exc.status_code, exc.detail)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        detail = str(exc.detail) if exc.detail else "Erro na requisicao."
        return _error_response(request, exc.status_code, detail)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error", extra={"path": request.url.path})
        return _error_response(request, 500, "Erro interno. Tente novamente.")
