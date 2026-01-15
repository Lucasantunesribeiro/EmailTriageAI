from app.clients.gemini_client import classify_and_reply
from app.schemas.triage import EmailTriageResult


class LLMService:
    def classify_and_reply(self, email_original: str, email_clean: str) -> EmailTriageResult:
        return classify_and_reply(email_original=email_original, email_clean=email_clean)
