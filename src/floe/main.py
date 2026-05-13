import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from floe import config
from floe.bot.commands import (
    cmd_budget,
    cmd_delete,
    cmd_export,
    cmd_help,
    cmd_start,
    cmd_summary,
    cmd_weekly,
)
from floe.bot.handlers import handle_photo, handle_text
from floe.scheduler.jobs import register_jobs

# Setup logging — tampil di console, berguna untuk debugging
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _setup_webhook(app: Application, bot_token: str, webhook_url: str) -> None:
    full_url = f"{webhook_url.rstrip('/')}/{bot_token}"
    logger.info("\U0001f310 Webhook aktif: %s (port %d)", full_url, config.PORT)
    app.run_webhook(
        listen="0.0.0.0",
        port=config.PORT,
        url_path=bot_token,
        webhook_url=full_url,
        secret_token=config.WEBHOOK_SECRET,
        drop_pending_updates=True,
    )


def main() -> None:
    logger.info("\U0001f300 Floe Finance Tracker starting up...")

    if not config.ALLOWED_USER_IDS:
        logger.warning(
            "ALLOWED_USER_IDS is empty -- no users will be able to use the bot. "
            "Set ALLOWED_USER_IDS in .env to grant access."
        )

    bot_token = config.TELEGRAM_BOT_TOKEN.get_secret_value()
    app = Application.builder().token(bot_token).build()

    # --- Daftarkan Command Handlers ---
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("weekly", cmd_weekly))
    app.add_handler(CommandHandler("delete", cmd_delete))
    app.add_handler(CommandHandler("export", cmd_export))
    app.add_handler(CommandHandler("budget", cmd_budget))

    # --- Daftarkan Message Handlers ---
    # Foto harus didaftarkan SEBELUM teks umum
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # --- Daftarkan Scheduled Jobs ---
    register_jobs(app)

    webhook_url = config.WEBHOOK_URL
    if webhook_url:
        _setup_webhook(app, bot_token, webhook_url)
    else:
        logger.info("\u2705 Bot siap. Mulai polling...")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
