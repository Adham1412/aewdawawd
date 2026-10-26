from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "StarMarket"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./starmarket_dev.db"
    bot_token: str = ""
    telegram_bot_username: str = ""
    miniapp_url: str = ""
    admin_url: str = ""
    payment_instructions: str = ""
    session_secret: str = ""
    session_ttl_seconds: int = 3600
    telegram_initdata_max_age_seconds: int = 86400
    admin_telegram_ids: str = ""
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    mock_payments_enabled: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def admin_ids(self) -> set[int]:
        return {int(x.strip()) for x in self.admin_telegram_ids.split(",") if x.strip().isdigit()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

    def validate_production_secrets(self) -> None:
        if self.app_env.lower() == "production":
            if len(self.session_secret) < 32 or self.session_secret.startswith("replace-with-"):
                raise RuntimeError("SESSION_SECRET must be at least 32 characters in production")
            if not self.bot_token:
                raise RuntimeError("BOT_TOKEN is required in production")
            if not self.admin_ids:
                raise RuntimeError("ADMIN_TELEGRAM_IDS is required in production (nobody could process orders)")
            if self.mock_payments_enabled:
                raise RuntimeError("MOCK_PAYMENTS_ENABLED must be false in production")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
