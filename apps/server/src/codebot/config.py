"""CodeBot server configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file.

    All settings can be overridden via environment variables prefixed with
    ``CODEBOT_``. For example, ``CODEBOT_DATABASE_URL`` overrides ``database_url``.
    """

    model_config = SettingsConfigDict(
        env_prefix="CODEBOT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://codebot:codebot_dev@localhost:5433/codebot"

    # Cache / Pub-Sub
    redis_url: str = "redis://localhost:6379/0"

    # Event Bus
    nats_url: str = "nats://localhost:4222"

    # Embedded Vector Store (LanceDB — runs in-process, no Docker service needed)
    lancedb_path: str = "data/lancedb"

    # LLM Configuration
    llm_config_path: str = "configs/providers/llm.yaml"

    # Auth
    jwt_secret: str = "CHANGE-ME-IN-PRODUCTION-use-secrets-token-urlsafe-64"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Rate Limiting
    rate_limit_default: str = "60/minute"

    # Server
    debug: bool = True
    log_level: str = "INFO"


# Module-level singleton — import this from other modules.
settings = Settings()
