"""
Application configuration loaded from environment variables.
Copy src/.env.example to src/.env and fill in real values before running.

Active AI provider: Google Gemini (GEMINI_API_KEY / GEMINI_MODEL).
Legacy AI provider: DeepSeek (DEEPSEEK_API_KEY / DEEPSEEK_MODEL) — preserved
  for easy restoration; not used by the runtime path.

Usage anywhere in the app:
    from backend.app.config import settings
    print(settings.gemini_api_key)
"""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables or a .env file."""

    # ── Application ──────────────────────────────────────────────────────────
    app_name: str = "CourseGenie AI"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_port: int = 8000

    # ── Google Gemini AI (ACTIVE provider) ───────────────────────────────────
    gemini_api_key: str = ""
    # Default model — override via env var GEMINI_MODEL
    gemini_model: str = "gemini-1.5-flash"

    # ── DeepSeek AI (LEGACY — preserved for easy restoration) ────────────────
    deepseek_api_key: str = ""
    # Default model — can be overridden via env var DEEPSEEK_MODEL
    deepseek_model: str = "deepseek-chat"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql://coursegenie:changeme@localhost:5432/coursegenie"

    # ── Authentication (JWT) ─────────────────────────────────────────────────
    # Generate a strong key with: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080   # 7 days

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("gemini_api_key", "deepseek_api_key", mode="before")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern)."""
    return Settings()


# Module-level singleton — import this everywhere.
settings: Settings = get_settings()
