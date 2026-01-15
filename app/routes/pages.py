import json
import logging
from typing import Optional

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.clients.gemini_client import LLMQuotaError, LLMServiceError
from app.config import settings
from app.schemas.triage import TriageResponse
from app.services.analyzer_service import AnalyzerService
from app.utils.input_reader import extract_text_from_input
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
analyzer = AnalyzerService()
rate_limiter = RateLimiter(
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def _render_page(
    request: Request,
    result: Optional[TriageResponse] = None,
    error: Optional[str] = None,
) -> HTMLResponse:
    result_json = json.dumps(result.model_dump()) if result else "{}"
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result.result if result else None,
            "result_meta": result if result else None,
            "result_json": result_json,
            "error": error,
            "max_chars": settings.max_chars,
            "max_file_mb": settings.max_file_mb,
        },
    )


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return _render_page(request)


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    text_input: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> HTMLResponse:
    client_ip = _get_client_ip(request)
    if not rate_limiter.allow(client_ip):
        return _render_page(request, error="Muitas requisicoes. Tente novamente.")

    try:
        content, _source_file = await extract_text_from_input(file, text_input)
        if not content.strip():
            raise ValueError("Conteudo vazio")
        if len(content) > settings.max_chars:
            raise ValueError("Texto maior que o limite permitido")
        analysis = analyzer.analyze(content)
        result = TriageResponse(
            result=analysis.result,
            source=analysis.source,
            email_hash=analysis.email_hash,
            stats=analysis.stats,
            baseline_prob=analysis.baseline_prob,
        )
        return _render_page(request, result=result)
    except LLMQuotaError as exc:
        logger.warning("Analyze failed: quota", extra={"error": str(exc)})
        return _render_page(request, error=str(exc))
    except LLMServiceError as exc:
        logger.warning("Analyze failed: llm", extra={"error": str(exc)})
        return _render_page(request, error=str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Analyze failed", extra={"error": str(exc)})
        return _render_page(request, error=str(exc))
