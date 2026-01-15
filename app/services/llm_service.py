import concurrent.futures

from app.clients.gemini_client import LLMServiceError, classify_and_reply
from app.config import settings
from app.schemas.triage import EmailTriageResult


class LLMService:
    def classify_and_reply(
        self, email_original: str, email_clean: str
    ) -> EmailTriageResult:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                classify_and_reply,
                email_original=email_original,
                email_clean=email_clean,
            )
            try:
                return future.result(timeout=settings.llm_timeout_seconds)
            except concurrent.futures.TimeoutError as exc:
                raise LLMServiceError("Timeout ao consultar o LLM.") from exc
