from fastapi.testclient import TestClient

from app.schemas.triage import EmailTriageResult
from app.services.analyzer_service import AnalysisOutput
from app.utils.rate_limit import RateLimiter
from main import app


def _get_csrf_token(client: TestClient) -> str:
    response = client.get("/")
    assert response.status_code == 200
    token = response.cookies.get("csrf_token")
    assert token
    return token


def test_csrf_required_for_analyze() -> None:
    client = TestClient(app)
    response = client.post("/analyze", data={"text_input": "teste"})
    assert response.status_code == 403


def test_security_headers_present() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "Content-Security-Policy" in response.headers
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_upload_too_large() -> None:
    client = TestClient(app)
    token = _get_csrf_token(client)
    big_payload = b"a" * (2 * 1024 * 1024 + 1)
    response = client.post(
        "/api/analyze",
        data={"csrf_token": token},
        files={"file": ("big.txt", big_payload, "text/plain")},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 413


def test_invalid_pdf() -> None:
    client = TestClient(app)
    token = _get_csrf_token(client)
    response = client.post(
        "/api/analyze",
        data={"csrf_token": token},
        files={"file": ("bad.pdf", b"not pdf", "application/pdf")},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 400


def test_xss_escaped(monkeypatch) -> None:
    def fake_analyze(self, email_text: str) -> AnalysisOutput:
        result = EmailTriageResult(
            category="Produtivo",
            confidence=0.8,
            summary="<script>alert(1)</script>",
            suggested_reply="Obrigado, retornamos em breve.",
            tags=["status", "contrato", "prazo"],
            needs_human_review=False,
            reasons=["Solicita informacao", "Requer acao"],
        )
        return AnalysisOutput(
            result=result,
            source="llm",
            email_hash="hash",
            stats={"num_chars": len(email_text)},
            baseline_prob=None,
        )

    monkeypatch.setattr(
        "app.services.analyzer_service.AnalyzerService.analyze", fake_analyze
    )
    client = TestClient(app)
    token = _get_csrf_token(client)
    response = client.post(
        "/analyze", data={"text_input": "teste", "csrf_token": token}
    )
    assert response.status_code == 200
    assert "<script>alert(1)</script>" not in response.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in response.text


def test_rate_limit_api(monkeypatch) -> None:
    import app.routes.api as api_routes

    api_routes.rate_limiter = RateLimiter(limit=1, window_seconds=60)
    client = TestClient(app)
    token = _get_csrf_token(client)
    payload = {"text_input": "Status?", "csrf_token": token}
    headers = {"X-CSRF-Token": token}
    response_ok = client.post("/api/analyze", data=payload, headers=headers)
    response_block = client.post("/api/analyze", data=payload, headers=headers)
    assert response_ok.status_code in {200, 502, 429}
    assert response_block.status_code == 429
