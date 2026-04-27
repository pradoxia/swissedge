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

    # SEC EDGAR (email required by their API policy)
    sec_user_agent: str = ""

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
