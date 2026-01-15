import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.clients.gemini_client import LLMQuotaError, LLMServiceError
from app.config import settings
from app.schemas.triage import TriageResponse
from app.services.analyzer_service import AnalyzerService
from app.utils.input_reader import extract_text_from_input
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
analyzer = AnalyzerService()
rate_limiter = RateLimiter(
    limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window_seconds,
)


def _get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/api/analyze", response_model=TriageResponse)
async def analyze_api(
    request: Request,
    text_input: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> TriageResponse:
    client_ip = _get_client_ip(request)
    if not rate_limiter.allow(client_ip):
        raise HTTPException(status_code=429, detail="Muitas requisicoes")

    try:
        content, _source_file = await extract_text_from_input(file, text_input)
        if not content.strip():
            raise ValueError("Conteudo vazio")
        if len(content) > settings.max_chars:
            raise ValueError("Texto maior que o limite permitido")
        analysis = analyzer.analyze(content)
        return TriageResponse(
            result=analysis.result,
            source=analysis.source,
            email_hash=analysis.email_hash,
            stats=analysis.stats,
            baseline_prob=analysis.baseline_prob,
        )
    except LLMQuotaError as exc:
        logger.warning("API analyze failed: quota", extra={"error": str(exc)})
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except LLMServiceError as exc:
        logger.warning("API analyze failed: llm", extra={"error": str(exc)})
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("API analyze failed", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
