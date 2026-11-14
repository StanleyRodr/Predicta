"""Application settings, read once from the environment and ``backend/.env``.

This is the only module that reads environment variables. Every new variable
is declared here and in ``.env.example``.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qs, urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

Environment = Literal["development", "test", "production"]

DEFAULT_CORS_ORIGINS = ["http://localhost:5173"]
DEFAULT_TRUSTED_PROXIES = ["127.0.0.1"]

# Production refuses the .env.example placeholder and anything shorter.
SECRET_KEY_PLACEHOLDER = "CHANGE_ME_GENERATE_WITH_OPENSSL"  # noqa: S105 - placeholder that is rejected, not a secret
MIN_PRODUCTION_SECRET_LENGTH = 32
# libpq modes that refuse an unencrypted connection.
SECURE_SSL_MODES = {"require", "verify-ca", "verify-full"}

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
    # Proxies whose X-Forwarded-For is believed; "*" only when the app is
    # reachable solely through the provider's proxy (Railway).
    trusted_proxies: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: list(DEFAULT_TRUSTED_PROXIES)
    )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @field_validator("cors_origins", "trusted_proxies", mode="before")
    @classmethod
    def _split_on_commas(cls, value: object) -> object:
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

    @model_validator(mode="after")
    def _require_strong_secret_in_production(self) -> "Settings":
        if self.is_production and (
            len(self.secret_key) < MIN_PRODUCTION_SECRET_LENGTH or self.secret_key == SECRET_KEY_PLACEHOLDER
        ):
            raise ValueError(
                f"SECRET_KEY debe tener al menos {MIN_PRODUCTION_SECRET_LENGTH} caracteres en producción "
                "y no puede ser el valor de ejemplo; genera una con: openssl rand -hex 32"
            )
        return self

    @model_validator(mode="after")
    def _require_ssl_database_in_production(self) -> "Settings":
        if self.is_production:
            modes = parse_qs(urlsplit(self.database_url).query).get("sslmode", [])
            if not modes or modes[-1] not in SECURE_SSL_MODES:
                raise ValueError(
                    "DATABASE_URL debe incluir sslmode=require, verify-ca o verify-full en producción."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings, built on first use."""
    return Settings()  # type: ignore[call-arg]  # required values come from the environment


settings = get_settings()
