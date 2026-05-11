import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Environment variable '{key}' tidak diset. Cek file .env kamu.")
    return value


TELEGRAM_BOT_TOKEN: str = _require("TELEGRAM_BOT_TOKEN")

ALLOWED_USER_IDS: list[int] = [
    int(x.strip()) for x in _require("ALLOWED_USER_IDS").split(",") if x.strip()
]

GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")

SPREADSHEET_ID: str = _require("SPREADSHEET_ID")
GOOGLE_SERVICE_ACCOUNT_FILE: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

DAILY_SUMMARY_TIME: str = os.getenv("DAILY_SUMMARY_TIME", "21:00")
WEEKLY_SUMMARY_DAY: str = os.getenv("WEEKLY_SUMMARY_DAY", "sunday")
WEEKLY_SUMMARY_TIME: str = os.getenv("WEEKLY_SUMMARY_TIME", "20:00")
