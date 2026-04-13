from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    linq_api_key: str
    linq_webhook_secret: str = ""
    anthropic_api_key: str
    port: int = 8000
    cors_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
