import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from floe import config
from floe.ai.gemini import parse_image, parse_text
from floe.sheets.client import append_transaction

logger = logging.getLogger(__name__)


async def _check_access(update: Update) -> bool:
    """Cek apakah user terdaftar di whitelist. Kirim pesan tolak jika tidak."""
    user_id = update.effective_user.id
    if user_id not in config.ALLOWED_USER_IDS:
        logger.warning("Akses ditolak untuk user %s", user_id)
        await update.message.reply_text("🚫 Maaf, kamu belum terdaftar untuk menggunakan bot ini.")
        return False
    return True


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text
    if not message:
        return

    if not await _check_access(update):
        return

    logger.info(f"Pesan masuk dari {update.effective_user.id}: {message[:50]}")

    tx = parse_text(message)

    if tx is None:
        await update.message.reply_text(
            "🤔 Saya tidak bisa membaca transaksi dari pesan itu.\n"
            "Coba format seperti: `Makan siang 35rb` atau `Gaji 5jt`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    success = append_transaction(tx, user_id=update.effective_user.id)

    if success:
        await update.message.reply_text(
            f"✅ *Berhasil dicatat!*\n\n{tx.format_summary_line()}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text(
            "⚠️ Transaksi diparse tapi gagal disimpan ke Sheets. Cek log untuk detail."
        )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    photos = update.message.photo
    if not photos:
        return

    if not await _check_access(update):
        return

    photo_file = await photos[-1].get_file()

    logger.info(f"Foto masuk dari {update.effective_user.id}, file_id: {photos[-1].file_id}")

    await update.message.reply_text("📸 Sedang membaca foto...")

    image_bytes = await photo_file.download_as_bytearray()

    tx = parse_image(bytes(image_bytes), mime_type="image/jpeg")

    if tx is None:
        await update.message.reply_text(
            "🤔 Saya tidak bisa membaca transaksi dari foto ini.\n"
            "Pastikan foto cukup jelas dan berisi struk atau screenshot transfer."
        )
        return

    success = append_transaction(tx, user_id=update.effective_user.id)

    if success:
        await update.message.reply_text(
            f"✅ *Foto berhasil dicatat!*\n\n{tx.format_summary_line()}",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text("⚠️ Foto diparse tapi gagal disimpan ke Sheets.")
