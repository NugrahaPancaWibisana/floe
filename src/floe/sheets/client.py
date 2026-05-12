import logging
from datetime import datetime

import gspread
import polars as pl
from google.oauth2.service_account import Credentials
from gspread.utils import ValueInputOption

from floe import config
from floe.models import Transaction

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

BUDGET_HEADER = ["UserID", "Category", "Limit"]

HEADER_ROW = ["Date", "Amount", "Type", "Category", "Description", "Source", "Note", "Timestamp"]


def _user_tab_name(user_id: int) -> str:
    return f"Transactions - {user_id}"


def _ensure_user_tab(user_id: int) -> gspread.Worksheet:
    """Cari atau buat tab Transactions - {user_id} dengan header."""
    client = _get_client()
    sheet = client.open_by_key(config.SPREADSHEET_ID)
    tab_name = _user_tab_name(user_id)

    try:
        return sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=tab_name, rows=100, cols=len(HEADER_ROW))
        ws.append_row(HEADER_ROW, value_input_option=ValueInputOption.user_entered)
        logger.info("Tab baru dibuat: %s", tab_name)
        return ws


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def append_transaction(tx: Transaction, user_id: int) -> bool:
    try:
        ws = _ensure_user_tab(user_id)
        ws.append_row(tx.to_row(), value_input_option=ValueInputOption.user_entered)
        logger.info(f"Transaksi ditambahkan: {tx.description} - Rp {tx.amount:,}")
        return True
    except Exception as e:
        logger.error(f"Gagal menulis ke Sheets: {e}")
        return False


def get_transactions_today(user_id: int) -> pl.DataFrame:
    today = datetime.now().strftime("%d/%m/%Y")
    return _get_transactions_by_date(today, user_id)


def get_transactions_this_month(user_id: int) -> pl.DataFrame:
    try:
        ws = _ensure_user_tab(user_id)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)
        df = df.with_columns(pl.col("Date").str.strptime(pl.Date, "%d/%m/%Y", strict=False))
        now = datetime.now()
        df = df.filter(
            (pl.col("Date").dt.year() == now.year) & (pl.col("Date").dt.month() == now.month)
        )
        return df
    except Exception as e:
        logger.error(f"Gagal membaca transaksi bulanan: {e}")
        return pl.DataFrame()


def get_transactions_this_week(user_id: int) -> pl.DataFrame:
    try:
        ws = _ensure_user_tab(user_id)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)
        df = df.with_columns(pl.col("Date").str.strptime(pl.Date, "%d/%m/%Y", strict=False))
        cutoff = datetime.now().date()
        df = df.filter(pl.col("Date") >= pl.lit(cutoff).dt.offset_by("-7d"))
        return df
    except Exception as e:
        logger.error(f"Gagal membaca transaksi mingguan: {e}")
        return pl.DataFrame()


def _get_transactions_by_date(date_str: str, user_id: int) -> pl.DataFrame:
    try:
        ws = _ensure_user_tab(user_id)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)
        return df.filter(pl.col("Date") == date_str)
    except Exception as e:
        logger.error(f"Gagal membaca transaksi harian: {e}")
        return pl.DataFrame()


def delete_last_transaction(user_id: int) -> dict | None:
    """
    Hapus baris transaksi terakhir dari tab user.
    Return dict dengan description dan amount jika berhasil, None jika kosong.
    """
    try:
        ws = _ensure_user_tab(user_id)
        all_values = ws.get_all_values()

        if len(all_values) <= 1:
            return None

        row_index = len(all_values)
        header = all_values[0]
        last_row = all_values[-1]

        description = last_row[header.index("Description")]
        amount = int(last_row[header.index("Amount")])

        ws.delete_rows(row_index)

        logger.info(f"Transaksi dihapus: {description} - Rp {amount:,}")
        return {"description": description, "amount": amount}
    except Exception as e:
        logger.error(f"Gagal menghapus transaksi: {e}")
        return None


def _ensure_budgets_tab() -> gspread.Worksheet:
    """Cari atau buat tab Budgets dengan header."""
    client = _get_client()
    sheet = client.open_by_key(config.SPREADSHEET_ID)

    try:
        return sheet.worksheet("Budgets")
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title="Budgets", rows=100, cols=len(BUDGET_HEADER))
        ws.append_row(BUDGET_HEADER, value_input_option=ValueInputOption.user_entered)
        logger.info("Tab Budgets dibuat")
        return ws


def set_budget(user_id: int, category: str, limit: int) -> None:
    """Set atau update budget limit untuk user + kategori."""
    ws = _ensure_budgets_tab()
    records = ws.get_all_records()

    for i, row in enumerate(records, start=2):
        if int(row["UserID"]) == user_id and row["Category"] == category:
            ws.update(
                values=[[limit]],
                range_name=f"C{i}",
                value_input_option=ValueInputOption.user_entered,
            )
            logger.info("Budget diupdate: user=%s category=%s limit=%s", user_id, category, limit)
            return

    ws.append_row([user_id, category, limit], value_input_option=ValueInputOption.user_entered)
    logger.info("Budget ditambahkan: user=%s category=%s limit=%s", user_id, category, limit)


def get_budgets(user_id: int) -> dict[str, int]:
    """Ambil semua budget limit untuk user tertentu."""
    ws = _ensure_budgets_tab()
    records = ws.get_all_records()
    return {
        str(row["Category"]): int(row["Limit"]) for row in records if int(row["UserID"]) == user_id
    }


def check_budget_alert(user_id: int, category: str) -> str | None:
    """Cek apakah pengeluaran bulan ini di kategori melebihi budget.
    Return pesan alert jika ya, None jika aman atau tidak ada budget."""
    budgets = get_budgets(user_id)
    if category not in budgets:
        return None

    limit = budgets[category]
    df = get_transactions_this_month(user_id)
    if df.is_empty():
        return None

    spent = int(
        df.filter((pl.col("Category") == category) & (pl.col("Type") == "pengeluaran"))[
            "Amount"
        ].sum()
    )

    if spent > limit:
        return (
            f"⚠️ *Peringatan Budget!*\n\n"
            f"Kategori *{category}* sudah melebihi budget bulan ini:\n"
            f"• Budget: Rp {limit:,}\n"
            f"• Terpakai: Rp {spent:,}\n"
            f"• Lebih: Rp {spent - limit:,}"
        )
    return None


def compute_summary(df: pl.DataFrame) -> dict:
    if df.is_empty():
        return {"total_in": 0, "total_out": 0, "net": 0, "by_category": {}}

    required_columns = {"Amount", "Type", "Category"}
    if not required_columns.issubset(df.columns):
        return {"total_in": 0, "total_out": 0, "net": 0, "by_category": {}}

    df = df.with_columns(pl.col("Amount").cast(pl.Int64, strict=False).fill_null(0))

    total_in = df.filter(pl.col("Type") == "pemasukan")["Amount"].sum()
    total_out = df.filter(pl.col("Type") == "pengeluaran")["Amount"].sum()

    by_category = (
        df.filter(pl.col("Type") == "pengeluaran")
        .group_by("Category")
        .agg(pl.col("Amount").sum())
        .sort("Amount", descending=True)
        .to_dicts()
    )

    return {
        "total_in": total_in,
        "total_out": total_out,
        "net": int(total_in) - int(total_out),
        "by_category": {row["Category"]: row["Amount"] for row in by_category},
    }
