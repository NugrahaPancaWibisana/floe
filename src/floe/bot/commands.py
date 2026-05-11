import io
import logging
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from floe.sheets.client import (
    compute_summary,
    delete_last_transaction,
    get_transactions_this_month,
    get_transactions_this_week,
    get_transactions_today,
)

logger = logging.getLogger(__name__)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    text = (
        f"🌊 *Selamat datang, {user.first_name}!*\n\n"
        "Saya akan mencatat keuangan kamu secara otomatis.\n\n"
        "*Cara pakai:*\n"
        "• Kirim pesan teks: `Makan siang 35rb`\n"
        "• Kirim foto struk atau screenshot transfer\n\n"
        "*Perintah tersedia:*\n"
        "/summary — Ringkasan hari ini\n"
        "/weekly — Ringkasan 7 hari terakhir\n"
        "/export — Ekspor CSV bulan ini\n"
        "/help — Bantuan lengkap\n\n"
        "_Mulai catat sekarang!_"
    )
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None:
        return
    text = (
        "📖 *Panduan Floe*\n\n"
        "*Format teks yang bisa kamu kirim:*\n"
        "• `Makan siang 35rb`\n"
        "• `Beli bensin 50000`\n"
        "• `Gaji masuk 5jt`\n"
        "• `Bayar listrik 250.000`\n\n"
        "*Format tanggal (opsional):*\n"
        "• `Kemarin makan malam 40rb`\n"
        "• `3 Januari makan 30000`\n\n"
        "*Foto:*\n"
        "Kirim foto struk belanja atau screenshot transfer bank — "
        "saya akan otomatis membaca dan mencatatnya.\n\n"
        "*Perintah:*\n"
        "/summary — Ringkasan pengeluaran hari ini\n"
        "/weekly — Ringkasan 7 hari terakhir\n"
        "/export — Ekspor CSV bulan ini\n"
    )
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    await message.reply_text("⏳ Mengambil data...")
    df = get_transactions_today(user_id=user.id)
    text = _format_summary(df, label="Hari Ini")
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    await message.reply_text("⏳ Mengambil data...")
    df = get_transactions_this_week(user_id=user.id)
    text = _format_summary(df, label="7 Hari Terakhir")
    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    result = delete_last_transaction(user_id=user.id)

    if result is None:
        await message.reply_text("📭 Belum ada transaksi yang bisa dihapus.")
        return

    await message.reply_text(
        f"🗑️ *Transaksi dihapus:*\n\n➖ *{result['description']}*\n   Rp {result['amount']:,}",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        return
    await message.reply_text("⏳ Mengambil data...")

    df = get_transactions_this_month(user_id=user.id)

    if df.is_empty():
        await message.reply_text("📭 Belum ada transaksi bulan ini.")
        return

    now = datetime.now()
    csv_bytes = df.write_csv().encode()
    await message.reply_document(
        document=io.BytesIO(csv_bytes),
        filename=f"floe_{now.year}_{now.month:02d}.csv",
    )


def _format_summary(df, label: str) -> str:
    summary = compute_summary(df)

    if summary["total_out"] == 0 and summary["total_in"] == 0:
        return f"📭 Belum ada transaksi untuk {label.lower()}."

    lines = [f"📊 *Ringkasan {label}*\n"]

    if summary["total_in"] > 0:
        lines.append(f"💚 Pemasukan: *Rp {summary['total_in']:,}*")
    if summary["total_out"] > 0:
        lines.append(f"❤️ Pengeluaran: *Rp {summary['total_out']:,}*")

    net = summary["net"]
    sign = "+" if net >= 0 else ""
    lines.append(f"📈 Saldo: *{sign}Rp {net:,}*")

    if summary["by_category"]:
        lines.append("\n*Rincian pengeluaran:*")
        for cat, amt in summary["by_category"].items():
            lines.append(f"  • {cat}: Rp {amt:,}")

    return "\n".join(lines)
