"""
Application configuration loaded from environment variables.
Copy src/.env.example to src/.env and fill in real values before running.

All watsonx.ai and database credentials live here so nothing else in the
codebase touches os.environ directly.

Usage anywhere in the app:
    from backend.app.config import settings
    print(settings.watsonx_url)
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

    # ── IBM watsonx.ai ───────────────────────────────────────────────────────
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    # Default model — can be overridden via env var WATSONX_MODEL_ID
    watsonx_model_id: str = "ibm/granite-13b-instruct-v2"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = "postgresql://coursegenie:changeme@localhost:5432/coursegenie"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("watsonx_api_key", "watsonx_project_id", mode="before")
    @classmethod
    def _strip_whitespace(cls, v: str) -> str:
        return v.strip() if isinstance(v, str) else v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern)."""
    return Settings()


# Module-level singleton — import this everywhere.
settings: Settings = get_settings()
