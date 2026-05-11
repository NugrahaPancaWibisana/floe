import logging

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from floe import config
from floe.bot.commands import cmd_delete, cmd_help, cmd_start, cmd_summary, cmd_weekly
from floe.bot.handlers import handle_photo, handle_text
from floe.scheduler.jobs import register_jobs

# Setup logging — tampil di console, berguna untuk debugging
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("\U0001f300 Floe Finance Tracker starting up...")

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # --- Daftarkan Command Handlers ---
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("summary", cmd_summary))
    app.add_handler(CommandHandler("weekly", cmd_weekly))
    app.add_handler(CommandHandler("delete", cmd_delete))

    # --- Daftarkan Message Handlers ---
    # Foto harus didaftarkan SEBELUM teks umum
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # --- Daftarkan Scheduled Jobs ---
    register_jobs(app)

    logger.info("\u2705 Bot siap. Mulai polling...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
