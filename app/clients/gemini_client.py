import json
import logging
from typing import Optional

from google import genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
from google.genai import types

from app.config import settings
from app.schemas.triage import EmailTriageResult

logger = logging.getLogger(__name__)

_client: Optional[genai.Client] = None

SYSTEM_PROMPT = (
    "Voce e um assistente de triagem de emails corporativos. "
    "Classifique emails como Produtivo ou Improdutivo seguindo as regras: "
    "Produtivo pede acao, status, suporte, arquivo, problema ou solicitacao. "
    "Improdutivo sao felicitacoes, agradecimentos, ruido ou assuntos fora do tema. "
    "Se estiver ambiguo, defina needs_human_review=true e confidence < 0.6. "
    "A resposta sugerida deve ser curta, objetiva, educada e em PT-BR. "
    "Nunca invente detalhes ou prazos. "
    "Se for improdutivo, responda com educacao e encerre."
)


class LLMServiceError(RuntimeError):
    pass


class LLMQuotaError(LLMServiceError):
    pass


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = settings.gemini_api_key or None
        if not api_key:
            raise LLMServiceError("GEMINI_API_KEY nao configurada.")
        _client = genai.Client(api_key=api_key)
    return _client


def _parse_json_response(text: str) -> EmailTriageResult:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]

    data = json.loads(cleaned)
    return EmailTriageResult.model_validate(data)


def classify_and_reply(email_original: str, email_clean: str) -> EmailTriageResult:
    user_prompt = (
        "Retorne APENAS JSON valido com as chaves: "
        "category, confidence, summary, suggested_reply, tags, "
        "needs_human_review, reasons. "
        "category deve ser Produtivo ou Improdutivo. "
        "confidence deve ser float entre 0 e 1. "
        "summary ate 200 caracteres. "
        "suggested_reply ate 700 caracteres. "
        "tags deve ter 3 a 8 strings. "
        "reasons deve ter 2 a 5 strings. "
        "\n\nEmail original:\n"
        f"{email_original}\n\n"
        "Email preprocessado:\n"
        f"{email_clean}\n"
    )

    try:
        client = _get_client()
        logger.info(f"Using Gemini model: {settings.gemini_model}")
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        if not response or not getattr(response, "text", None):
            raise LLMServiceError("Resposta vazia do Gemini.")
        return _parse_json_response(response.text)
    except ResourceExhausted as exc:
        logger.warning("Gemini quota exceeded")
        raise LLMQuotaError(
            "Limite de uso do Gemini atingido. Verifique sua cota e tente novamente."
        ) from exc
    except (GoogleAPIError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Gemini API error")
        raise LLMServiceError(f"Falha ao consultar o LLM: {exc}") from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("LLM request failed")
        raise LLMServiceError(f"Falha ao consultar o LLM: {exc}") from exc
