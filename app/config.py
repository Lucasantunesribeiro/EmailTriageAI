import json
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"
    app_name: str = "EmailTriageAI"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    max_chars: int = 40000
    max_extracted_chars: int = 40000
    max_file_mb: int = 2
    max_body_mb: int = 3
    max_pdf_pages: int = 10
    pdf_timeout_seconds: float = 4.0
    llm_timeout_seconds: float = 12.0
    rate_limit_window_seconds: int = 60
    rate_limit_analyze: int = 10
    rate_limit_api: int = 5
    rate_limit_feedback: int = 30
    baseline_threshold: float = 0.85
    log_level: str = "INFO"
    allowed_hosts: List[str] = ["localhost", "127.0.0.1", "testserver"]
    cors_allow_origins: List[str] = []
    force_https: bool = False
    enable_hsts: bool = False
    hsts_max_age: int = 31_536_000
    session_secret: str = "dev-secret-change"
    session_cookie: str = "emailtriageai_session"
    session_max_age: int = 3600
    csrf_cookie_name: str = "csrf_token"
    csrf_cookie_samesite: str = "lax"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
        env_ignore_empty=True,
        enable_decoding=False,
    )

    @field_validator("allowed_hosts", "cors_allow_origins", mode="before")
    @classmethod
    def split_csv(cls, value):
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed.startswith("[") and trimmed.endswith("]"):
                try:
                    parsed = json.loads(trimmed)
                except ValueError:
                    parsed = None
                if isinstance(parsed, list):
                    return parsed
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("csrf_cookie_samesite", mode="before")
    @classmethod
    def normalize_samesite(cls, value):
        if isinstance(value, str):
            return value.lower()
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def secure_cookies(self) -> bool:
        return self.is_production

    @property
    def hsts_enabled(self) -> bool:
        return self.enable_hsts or self.is_production

    @property
    def https_redirect_enabled(self) -> bool:
        return self.force_https or self.is_production

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024

    @property
    def max_body_bytes(self) -> int:
        return self.max_body_mb * 1024 * 1024

    @model_validator(mode="after")
    def allow_testserver_in_dev(self):
        if not self.is_production and "testserver" not in self.allowed_hosts:
            self.allowed_hosts.append("testserver")
        return self


settings = Settings()
