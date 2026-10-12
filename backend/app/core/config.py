"""Application configuration and settings management."""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core environment
    app_name: str = "TensorFoundry"
    app_version: str = "1.0.0"
    app_env: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # Author & Portfolio Identity
    author_name: str = "Alan Vo"
    author_email: str = "alanvo@gmail.com"
    github_owner: str = "ALANDVO"

    # Local Demo Mode: Binds strictly to local environment, refused in production
    demo_mode: bool = Field(default=True, alias="DEMO_MODE")
    demo_jwt_secret: str = Field(
        default="local-dev-jwt-secret-tensor-foundry-2026-safe-dev-only",
        alias="DEMO_JWT_SECRET"
    )

    # Persistent Storage
    database_url: str = Field(
        default="sqlite:///./tensor_foundry.db",
        alias="DATABASE_URL"
    )

    # Keycloak OIDC Authentication Settings
    oidc_issuer_url: str = Field(
        default="http://127.0.0.1:8080/realms/tensor-foundry",
        alias="OIDC_ISSUER_URL"
    )
    oidc_audience: str = Field(
        default="tensor-foundry-api",
        alias="OIDC_AUDIENCE"
    )
    oidc_client_id: str = Field(
        default="tensor-foundry-client",
        alias="OIDC_CLIENT_ID"
    )
    oidc_jwks_url: str = Field(
        default="http://127.0.0.1:8080/realms/tensor-foundry/protocol/openid-connect/certs",
        alias="OIDC_JWKS_URL"
    )
    oidc_token_url: str = Field(
        default="http://127.0.0.1:8080/realms/tensor-foundry/protocol/openid-connect/token",
        alias="OIDC_TOKEN_URL"
    )

    # Opt-in Advisory LLM Configuration (Keys only server-side, blank by default)
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_provider: str = Field(default="openai-compatible", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="LLM_BASE_URL"
    )
    llm_timeout_seconds: float = Field(default=15.0, alias="LLM_TIMEOUT_SECONDS")

    # CORS configuration
    cors_origins: List[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8000",
    ]

    def validate_production_guards(self) -> None:
        """Enforce strict security guards on startup."""
        if self.app_env.lower() in ("production", "prod"):
            if self.demo_mode:
                raise RuntimeError(
                    "CRITICAL SECURITY CONFIGURATION ERROR: Demo mode is strictly forbidden in production. "
                    "Set DEMO_MODE=false to start in production environment."
                )


settings = Settings()
