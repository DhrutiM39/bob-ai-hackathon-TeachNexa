"""
Application configuration loaded from environment variables.
Copy src/.env.example to src/.env and fill in real values before running.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables or a .env file."""

    # Application
    app_name: str = "CourseGenie AI"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_port: int = 8000

    # IBM watsonx.ai (populated later)
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"

    # Database (populated later)
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file="src/.env",
        env_file_encoding="utf-8",
        # Allow extra fields so future .env keys don't cause validation errors
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton pattern)."""
    return Settings()
