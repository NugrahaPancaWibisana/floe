import sys
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class _Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        hide_input_in_errors=True,
    )

    TELEGRAM_BOT_TOKEN: SecretStr = Field(default=SecretStr(""))
    ALLOWED_USER_IDS: list[int] = Field(default_factory=list)
    GEMINI_API_KEY: SecretStr = Field(default=SecretStr(""))
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"
    SPREADSHEET_ID: str = ""
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "service_account.json"
    WEBHOOK_URL: str | None = None
    WEBHOOK_SECRET: str | None = None
    PORT: int = 8080
    DAILY_SUMMARY_TIME: str = "21:00"
    WEEKLY_SUMMARY_DAY: str = "sunday"
    WEEKLY_SUMMARY_TIME: str = "20:00"

    @field_validator("ALLOWED_USER_IDS", mode="before")
    @classmethod
    def _split_ids(cls, v: str | int | list) -> list[int]:
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v


_settings = _Settings()

if not _settings.TELEGRAM_BOT_TOKEN.get_secret_value():
    sys.exit("Fatal: TELEGRAM_BOT_TOKEN tidak diset di .env")
if not _settings.GEMINI_API_KEY.get_secret_value():
    sys.exit("Fatal: GEMINI_API_KEY tidak diset di .env")

TELEGRAM_BOT_TOKEN: SecretStr = _settings.TELEGRAM_BOT_TOKEN
ALLOWED_USER_IDS: list[int] = _settings.ALLOWED_USER_IDS
GEMINI_API_KEY: SecretStr = _settings.GEMINI_API_KEY
GEMINI_MODEL: str = _settings.GEMINI_MODEL
SPREADSHEET_ID: str = _settings.SPREADSHEET_ID
GOOGLE_SERVICE_ACCOUNT_FILE: str = _settings.GOOGLE_SERVICE_ACCOUNT_FILE
WEBHOOK_URL: str | None = _settings.WEBHOOK_URL
WEBHOOK_SECRET: str | None = _settings.WEBHOOK_SECRET
PORT: int = _settings.PORT
DAILY_SUMMARY_TIME: str = _settings.DAILY_SUMMARY_TIME
WEEKLY_SUMMARY_DAY: str = _settings.WEEKLY_SUMMARY_DAY
WEEKLY_SUMMARY_TIME: str = _settings.WEEKLY_SUMMARY_TIME
