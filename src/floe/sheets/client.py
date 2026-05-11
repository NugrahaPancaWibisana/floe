import logging
from datetime import datetime

import gspread
import polars as pl
from google.oauth2.service_account import Credentials

from floe import config
from floe.models import Transaction

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_TRANSACTIONS = "Transactions"
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
        ws.append_row(HEADER_ROW, value_input_option="USER_ENTERED")
        logger.info("Tab baru dibuat: %s", tab_name)
        return ws


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(
        config.GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def append_transaction(tx: Transaction) -> bool:
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
        ws.append_row(tx.to_row(), value_input_option="USER_ENTERED")
        logger.info(f"Transaksi ditambahkan: {tx.description} - Rp {tx.amount:,}")
        return True
    except Exception as e:
        logger.error(f"Gagal menulis ke Sheets: {e}")
        return False


def get_transactions_today(user_id: int | None = None) -> pl.DataFrame:
    today = datetime.now().strftime("%d/%m/%Y")
    return _get_transactions_by_date(today, user_id=user_id)


def get_transactions_this_week(user_id: int | None = None) -> pl.DataFrame:
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)

        if user_id is not None:
            df = df.filter(pl.col("User ID") == user_id)

        df = df.with_columns(pl.col("Date").str.strptime(pl.Date, "%d/%m/%Y", strict=False))
        cutoff = datetime.now().date()
        df = df.filter(pl.col("Date") >= pl.lit(cutoff).dt.offset_by("-7d"))
        return df
    except Exception as e:
        logger.error(f"Gagal membaca transaksi mingguan: {e}")
        return pl.DataFrame()


def _get_transactions_by_date(date_str: str, user_id: int | None = None) -> pl.DataFrame:
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)

        if user_id is not None:
            df = df.filter(pl.col("User ID") == user_id)

        return df.filter(pl.col("Date") == date_str)
    except Exception as e:
        logger.error(f"Gagal membaca transaksi harian: {e}")
        return pl.DataFrame()


def delete_last_transaction(user_id: int) -> dict | None:
    """
    Hapus baris transaksi terakhir milik user_id dari sheet Transactions.
    Return dict dengan description dan amount jika berhasil, None jika kosong.
    """
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)

        all_values = ws.get_all_values()
        if len(all_values) <= 1:
            return None

        header = all_values[0]
        user_id_col = header.index("User ID")

        # Cari baris transaksi terakhir milik user_id
        target_row: int | None = None
        for i in range(len(all_values) - 1, 0, -1):
            row = all_values[i]
            if len(row) > user_id_col and row[user_id_col] == str(user_id):
                target_row = i + 1  # 1-indexed untuk Sheets API
                break

        if target_row is None:
            return None

        description = all_values[target_row - 1][header.index("Description")]
        amount = int(all_values[target_row - 1][header.index("Amount")])

        ws.delete_rows(target_row)

        logger.info(f"Transaksi dihapus: {description} - Rp {amount:,}")
        return {"description": description, "amount": amount}
    except Exception as e:
        logger.error(f"Gagal menghapus transaksi: {e}")
        return None


def get_unique_user_ids() -> list[int]:
    """Ambil semua unique user_id dari sheet Transactions."""
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
        records = ws.get_all_records()

        if not records:
            return []

        df = pl.DataFrame(records)
        user_ids = df["User ID"].unique().cast(pl.Int64).to_list()
        return [int(uid) for uid in user_ids]
    except Exception as e:
        logger.error(f"Gagal membaca user_ids: {e}")
        return []


def compute_summary(df: pl.DataFrame) -> dict:
    if df.is_empty():
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
        "net": total_in - total_out,
        "by_category": {row["Category"]: row["Amount"] for row in by_category},
    }
