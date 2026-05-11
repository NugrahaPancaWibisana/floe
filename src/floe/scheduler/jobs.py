import logging
from datetime import time

import pytz
from telegram.constants import ParseMode
from telegram.ext import Application

from floe import config
from floe.bot.commands import _format_summary
from floe.sheets.client import get_transactions_this_week, get_transactions_today

logger = logging.getLogger(__name__)

WIB = pytz.timezone("Asia/Jakarta")


def _parse_time(time_str: str) -> time:
    h, m = map(int, time_str.split(":"))
    return time(hour=h, minute=m, tzinfo=WIB)


async def job_daily_summary(context) -> None:
    logger.info("Menjalankan daily summary job...")
    df = get_transactions_today()
    text = "🌙 *Ringkasan Harian Floe*\n\n" + _format_summary(df, label="Hari Ini")

    await context.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


async def job_weekly_summary(context) -> None:
    logger.info("Menjalankan weekly summary job...")
    df = get_transactions_this_week()
    text = "📅 *Ringkasan Mingguan Floe*\n\n" + _format_summary(df, label="7 Hari Terakhir")

    await context.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
    )


def register_jobs(app: Application) -> None:
    job_queue = app.job_queue

    daily_time = _parse_time(config.DAILY_SUMMARY_TIME)
    job_queue.run_daily(
        job_daily_summary,
        time=daily_time,
        name="daily_summary",
    )
    logger.info(f"Daily summary dijadwalkan pukul {config.DAILY_SUMMARY_TIME} WIB")

    day_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
    weekly_day = day_map.get(config.WEEKLY_SUMMARY_DAY.lower(), 6)
    weekly_time = _parse_time(config.WEEKLY_SUMMARY_TIME)

    job_queue.run_daily(
        job_weekly_summary,
        time=weekly_time,
        days=(weekly_day,),
        name="weekly_summary",
    )
    logger.info(
        f"Weekly summary dijadwalkan hari {config.WEEKLY_SUMMARY_DAY} "
        f"pukul {config.WEEKLY_SUMMARY_TIME} WIB"
    )
