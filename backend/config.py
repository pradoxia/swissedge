from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://swissedge:swissedge@localhost:5432/swissedge"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Telegram
    telegram_bot_token: str = ""

    # AI Providers
    ai_provider: str = "openai"  # openai | anthropic
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ai_live_enabled: bool = False
    ai_openai_model: str = "gpt-4o-mini"
    ai_anthropic_model: str = "claude-haiku-4-5-20251001"
    ai_task_model_overrides: dict[str, str] = {}
    ai_daily_budget_usd: float = 0.0

    # SEC EDGAR (email required by their API policy)
    sec_user_agent: str = ""
    # W1: automatic SEC document acquisition after detection (Dani-approved).
    # Operational off-switch; acquired evidence remains unverified either way.
    auto_acquire_documents: bool = True

    # App
    debug: bool = False
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
