"""Application settings, read once from the environment and ``backend/.env``.

This is the only module that reads environment variables. Every new variable
is declared here and in ``.env.example``.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "test", "production"]

DEFAULT_CORS_ORIGINS = ["http://localhost:5173"]

# backend/.env, wherever the process starts; real environment variables win.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Typed configuration. Missing required values abort startup."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    database_url: str
    secret_key: str = Field(min_length=1)
    access_token_expire_minutes: int = Field(30, gt=0)
    # Unset means production: a deployment must opt in to development rules.
    environment: Environment = "production"
    # Comma-separated in the environment; "*" is accepted only in development.
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=lambda: list(DEFAULT_CORS_ORIGINS))
    log_level: str = "INFO"
    max_upload_rows: int = Field(200_000, gt=0)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _reject_wildcard_outside_development(self) -> "Settings":
        if "*" in self.cors_origins and self.environment != "development":
            raise ValueError(
                "CORS_ORIGINS='*' solo se permite con ENVIRONMENT=development; "
                "declara los orígenes del frontend separados por comas."
            )
        if not self.cors_origins:
            raise ValueError("CORS_ORIGINS no puede quedar vacío.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built on first use."""
    return Settings()  # type: ignore[call-arg]  # required values come from the environment


settings = get_settings()
