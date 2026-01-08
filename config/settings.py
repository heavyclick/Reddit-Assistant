from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_ANON_KEY: str

    # LLM Provider
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "gemini"  # "gemini" or "openai"
    LLM_MODEL: str = "gemini-2.0-flash-exp"
    LLM_TEMPERATURE: float = 0.9
    LLM_MAX_TOKENS: int = 500

    # Slack Notifications
    SLACK_WEBHOOK_URL: str
    SLACK_CHANNEL: str = "#reddit-assistant"

    # Dashboard
    DASHBOARD_URL: str = "http://localhost:3000"

    # Auto-approve
    AUTO_APPROVE_TIMEOUT_MINUTES: int = 1

    # System
    ENVIRONMENT: str = "development"
    MAX_ACCOUNTS: int = 6
    DEFAULT_TIMEZONE: str = "America/New_York"
    LOG_LEVEL: str = "INFO"

    # Rate Limiting
    MAX_COMMENTS_PER_DAY_DEFAULT: int = 5
    MAX_POSTS_PER_WEEK_DEFAULT: int = 2
    MIN_HOURS_BETWEEN_COMMENTS: float = 2.0
    REDDIT_API_REQUESTS_PER_MINUTE: int = 60

    # Cron Schedules
    MONITOR_CRON_SCHEDULE: str = "*/30 * * * *"
    DRAFT_CRON_SCHEDULE: str = "*/45 * * * *"
    POST_CRON_SCHEDULE: str = "*/15 * * * *"
    TRACK_CRON_SCHEDULE: str = "0 */6 * * *"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
