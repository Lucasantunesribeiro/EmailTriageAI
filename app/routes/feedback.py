import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.security.csrf import validate_csrf
from app.security.exceptions import CSRFError, RateLimitError
from app.security.limits import RATE_LIMIT_FEEDBACK, RATE_LIMIT_WINDOW_SECONDS
from app.utils.rate_limit import RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()
rate_limiter = RateLimiter(
    limit=RATE_LIMIT_FEEDBACK,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)


class FeedbackPayload(BaseModel):
    email_hash: str = Field(min_length=8)
    correct_label: Literal["Produtivo", "Improdutivo"]
    previous_label: Optional[Literal["Produtivo", "Improdutivo"]] = None
    source: Optional[str] = None


def _feedback_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "feedback.csv"


def _ensure_feedback_file() -> None:
    path = _feedback_path()
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["timestamp", "email_hash", "correct_label", "previous_label", "source"]
        )


@router.post("/feedback")
async def feedback(request: Request, payload: FeedbackPayload) -> dict:
    client_ip = _get_client_ip(request)
    try:
        validate_csrf(request)
        if not rate_limiter.allow(client_ip):
            raise RateLimitError()
        _ensure_feedback_file()
        with _feedback_path().open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    datetime.utcnow().isoformat(),
                    payload.email_hash,
                    payload.correct_label,
                    payload.previous_label or "",
                    payload.source or "",
                ]
            )
        return {"status": "ok"}
    except (CSRFError, RateLimitError) as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except Exception as exc:  # noqa: BLE001
        logger.warning("Feedback failed", extra={"error": str(exc)})
        return {"status": "error"}


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
