from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram Bot
    telegram_bot_token: str

    # Database
    database_url: str

    # Redis
    redis_url: str

    # API
    public_base_url: str
    api_port: int = 8000

    # Bot
    bot_port: int = 8080

    # AI Coach
    ai_enabled: bool = False
    openai_api_key: str = ""
    ai_model: str = "gpt-4"

    # Payments
    telegram_stars_enabled: bool = True
    tips_hmac_secret: str  # HMAC secret for signing tips payloads (32+ bytes)

    # Security
    secret_key: str
    internal_bot_secret: str  # HMAC secret for bot->API authentication

    # Admin
    admin_user: str = "admin"
    admin_pass: str = "changeme"
    mod_chat_id: int | None = None  # Telegram chat ID for moderation alerts

    # Environment
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
