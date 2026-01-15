import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from starlette.datastructures import UploadFile

from app.clients.gemini_client import LLMQuotaError, LLMServiceError
from app.security.csrf import validate_csrf
from app.security.exceptions import (
    AppError,
    CSRFError,
    RateLimitError,
    UploadValidationError,
)
from app.security.limits import RATE_LIMIT_API, RATE_LIMIT_WINDOW_SECONDS
from app.schemas.triage import TriageResponse
from app.services.analyzer_service import AnalyzerService
from app.utils.input_reader import extract_text_from_input
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
analyzer = AnalyzerService()
rate_limiter = RateLimiter(
    limit=RATE_LIMIT_API,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/api/analyze", response_model=TriageResponse)
async def analyze_api(request: Request) -> TriageResponse:
    client_ip = _get_client_ip(request)
    try:
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            payload = await request.json()
            csrf_token = payload.get("csrf_token", "")
            text_input = payload.get("text_input")
            file = None
        else:
            form = await request.form()
            csrf_token = form.get("csrf_token", "")
            text_input = form.get("text_input")
            file = form.get("file")
            if not isinstance(file, UploadFile):
                file = None

        validate_csrf(request, csrf_token)
        if not rate_limiter.allow(client_ip):
            raise RateLimitError()
        content, _source_file = await extract_text_from_input(file, text_input)
        analysis = analyzer.analyze(content)
        return TriageResponse(
            result=analysis.result,
            source=analysis.source,
            email_hash=analysis.email_hash,
            stats=analysis.stats,
            baseline_prob=analysis.baseline_prob,
        )
    except (UploadValidationError, CSRFError, RateLimitError, AppError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except LLMQuotaError as exc:
        logger.warning("API analyze failed: quota", extra={"error": str(exc)})
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except LLMServiceError as exc:
        logger.warning("API analyze failed: llm", extra={"error": str(exc)})
        raise HTTPException(
            status_code=502, detail="Falha ao consultar o LLM."
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("API analyze failed", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail="Requisicao invalida.") from exc
