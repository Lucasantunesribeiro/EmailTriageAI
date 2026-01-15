import logging
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.clients.gemini_client import LLMQuotaError, LLMServiceError
from app.config import settings
from app.security.csrf import get_or_create_csrf_token, set_csrf_cookie, validate_csrf
from app.security.exceptions import (
    AppError,
    CSRFError,
    RateLimitError,
    UploadValidationError,
)
from app.security.limits import RATE_LIMIT_ANALYZE, RATE_LIMIT_WINDOW_SECONDS
from app.schemas.triage import TriageResponse
from app.services.analyzer_service import AnalyzerService
from app.utils.input_reader import extract_text_from_input
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
analyzer = AnalyzerService()
rate_limiter = RateLimiter(
    limit=RATE_LIMIT_ANALYZE,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


def _render_page(
    request: Request,
    result: Optional[TriageResponse] = None,
    error: Optional[str] = None,
    status_code: int = 200,
) -> HTMLResponse:
    csrf_token = get_or_create_csrf_token(request)
    result_payload = result.model_dump() if result else {}
    response = templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result.result if result else None,
            "result_meta": result if result else None,
            "result_payload": result_payload,
            "error": error,
            "max_chars": settings.max_chars,
            "max_file_mb": settings.max_file_mb,
            "csrf_token": csrf_token,
            "csp_nonce": getattr(request.state, "csp_nonce", ""),
        },
        status_code=status_code,
    )
    set_csrf_cookie(response, csrf_token)
    return response


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_page(request)


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    csrf_token: str = Form(default=""),
    text_input: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> HTMLResponse:
    client_ip = _get_client_ip(request)
    try:
        validate_csrf(request, csrf_token)
        if not rate_limiter.allow(client_ip):
            raise RateLimitError()
        content, _source_file = await extract_text_from_input(file, text_input)
        analysis = analyzer.analyze(content)
        result = TriageResponse(
            result=analysis.result,
            source=analysis.source,
            email_hash=analysis.email_hash,
            stats=analysis.stats,
            baseline_prob=analysis.baseline_prob,
        )
        return _render_page(request, result=result)
    except (UploadValidationError, CSRFError, RateLimitError, AppError) as exc:
        return _render_page(request, error=exc.detail, status_code=exc.status_code)
    except LLMQuotaError as exc:
        logger.warning("Analyze failed: quota", extra={"error": str(exc)})
        return _render_page(request, error=str(exc), status_code=429)
    except LLMServiceError as exc:
        logger.warning("Analyze failed: llm", extra={"error": str(exc)})
        return _render_page(request, error=str(exc), status_code=502)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Analyze failed", extra={"error": str(exc)})
        return _render_page(
            request, error="Falha ao analisar o email.", status_code=400
        )


@router.get("/health")
async def healthcheck() -> dict:
    return {"status": "ok"}
