from fastapi.testclient import TestClient

from app.schemas.triage import EmailTriageResult
from main import app


def test_api_analyze_text(monkeypatch) -> None:
    fake_result = EmailTriageResult(
        category="Produtivo",
        confidence=0.75,
        summary="Pedido de status de contrato",
        suggested_reply="Obrigado pelo contato. Vamos verificar e retornar.",
        tags=["status", "contrato", "urgente"],
        needs_human_review=False,
        reasons=["Solicita informacao", "Requer acao"],
    )

    def fake_classify(self, email_original: str, email_clean: str) -> EmailTriageResult:
        return fake_result

    monkeypatch.setattr(
        "app.services.llm_service.LLMService.classify_and_reply", fake_classify
    )

    client = TestClient(app)
    response = client.post("/api/analyze", data={"text_input": "Qual o status do pedido?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["result"]["category"] == "Produtivo"
    assert "suggested_reply" in payload["result"]
