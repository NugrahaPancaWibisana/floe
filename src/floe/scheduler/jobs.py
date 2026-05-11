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


async def _send_summary_to_users(context, get_transactions_fn, title: str, label: str) -> None:
    for uid in config.ALLOWED_USER_IDS:
        df = get_transactions_fn(user_id=uid)
        text = f"{title}\n\n" + _format_summary(df, label=label)
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            logger.error(f"Gagal kirim summary ke user {uid}: {e}")


async def job_daily_summary(context) -> None:
    logger.info("Menjalankan daily summary job...")
    await _send_summary_to_users(
        context,
        get_transactions_today,
        "🌙 *Ringkasan Harian Floe*",
        "Hari Ini",
    )


async def job_weekly_summary(context) -> None:
    logger.info("Menjalankan weekly summary job...")
    await _send_summary_to_users(
        context,
        get_transactions_this_week,
        "📅 *Ringkasan Mingguan Floe*",
        "7 Hari Terakhir",
    )


def register_jobs(app: Application) -> None:
    job_queue = app.job_queue
    if job_queue is None:
        logger.error("JobQueue tidak tersedia — scheduler tidak akan berjalan")
        return

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
