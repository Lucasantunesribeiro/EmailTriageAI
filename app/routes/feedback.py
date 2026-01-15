import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


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
        writer.writerow(["timestamp", "email_hash", "correct_label", "previous_label", "source"])


@router.post("/feedback")
async def feedback(payload: FeedbackPayload) -> dict:
    try:
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
    except Exception as exc:  # noqa: BLE001
        logger.warning("Feedback failed", extra={"error": str(exc)})
        return {"status": "error"}
