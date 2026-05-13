import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from floe import config
from floe.ai.gemini import parse_image, parse_text
from floe.models import Transaction, TransactionType
from floe.sheets.client import append_transaction, check_budget_alert

logger = logging.getLogger(__name__)


async def _check_access(update: Update) -> bool:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return False
    if user.id not in config.ALLOWED_USER_IDS:
        logger.warning("Akses ditolak untuk user %s", user.id)
        await message.reply_text("🚫 Maaf, kamu belum terdaftar untuk menggunakan bot ini.")
        return False
    return True


async def _process_transaction(
    tx: Transaction | None,
    update: Update,
    user_id: int,
    source_label: str = "Berhasil dicatat",
    parse_error_message: str | None = None,
) -> None:
    message = update.message
    if message is None:
        return

    if tx is None:
        await message.reply_text(
            parse_error_message
            or "🤔 Saya tidak bisa membaca transaksi dari pesan itu.\n"
            "Coba format seperti: `Makan siang 35rb` atau `Gaji 5jt`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    success = append_transaction(tx, user_id=user_id)

    if success:
        msg = f"✅ *{source_label}!*\n\n{tx.format_summary_line()}"
        alert = None
        if tx.type == TransactionType.PENGELUARAN:
            alert = check_budget_alert(user_id, tx.category)
        if alert:
            msg += f"\n\n{alert}"
        await message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text(
            "⚠️ Transaksi diparse tapi gagal disimpan ke Sheets. Cek log untuk detail."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return

    text = message.text
    if not text:
        return

    if not await _check_access(update):
        return

    logger.info("Pesan masuk dari %s: %s", user.id, text[:50])

    tx = parse_text(text)
    await _process_transaction(tx, update, user.id)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return

    photos = message.photo
    if not photos:
        return

    if not await _check_access(update):
        return

    photo_file = await photos[-1].get_file()

    logger.info("Foto masuk dari %s, file_id: %s", user.id, photos[-1].file_id)

    await message.reply_text("📸 Sedang membaca foto...")

    image_bytes = await photo_file.download_as_bytearray()

    tx = parse_image(bytes(image_bytes), mime_type="image/jpeg")
    await _process_transaction(
        tx,
        update,
        user.id,
        source_label="Foto berhasil dicatat",
        parse_error_message=(
            "🤔 Saya tidak bisa membaca transaksi dari foto ini.\n"
            "Pastikan foto cukup jelas dan berisi struk atau screenshot transfer."
        ),
    )
