from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EmailTriageAI"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash-002"
    max_chars: int = 40000
    max_file_mb: int = 2
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60
    baseline_threshold: float = 0.85
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    @property
    def max_file_bytes(self) -> int:
        return self.max_file_mb * 1024 * 1024


settings = Settings()
