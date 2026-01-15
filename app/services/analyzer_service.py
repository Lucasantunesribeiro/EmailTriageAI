import logging
from dataclasses import dataclass
from typing import Dict, Optional

from app.config import settings
from app.schemas.triage import EmailTriageResult
from app.services.baseline_service import BaselineService
from app.services.llm_service import LLMService
from app.utils.hashing import hash_text
from app.utils.preprocessing import preprocess_text

logger = logging.getLogger(__name__)


@dataclass
class AnalysisOutput:
    result: EmailTriageResult
    source: str
    email_hash: str
    stats: Dict[str, int]
    baseline_prob: Optional[float]


class AnalyzerService:
    def __init__(self) -> None:
        self.baseline_service = BaselineService()
        self.llm_service = LLMService()

    def analyze(self, email_text: str) -> AnalysisOutput:
        processed = preprocess_text(email_text)
        email_hash = hash_text(email_text)
        stats = processed["stats"]

        baseline_pred = self.baseline_service.predict(processed["clean_text"])
        llm_original = email_text[:12000]
        llm_clean = processed["clean_text"][:12000]
        llm_result = self.llm_service.classify_and_reply(llm_original, llm_clean)

        source = "llm"
        baseline_prob = None
        if baseline_pred and baseline_pred[1] >= settings.baseline_threshold:
            label, prob = baseline_pred
            llm_result.category = label
            llm_result.confidence = prob
            source = "baseline"
            baseline_prob = prob
        elif baseline_pred:
            baseline_prob = baseline_pred[1]

        logger.info(
            "Email analyzed",
            extra={
                "hash": email_hash,
                "num_chars": stats["num_chars"],
                "source": source,
            },
        )

        return AnalysisOutput(
            result=llm_result,
            source=source,
            email_hash=email_hash,
            stats=stats,
            baseline_prob=baseline_prob,
        )
