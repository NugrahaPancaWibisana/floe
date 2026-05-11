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


def get_transactions_today() -> pl.DataFrame:
    today = datetime.now().strftime("%d/%m/%Y")
    return _get_transactions_by_date(today)


def get_transactions_this_week() -> pl.DataFrame:
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
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


def _get_transactions_by_date(date_str: str) -> pl.DataFrame:
    try:
        client = _get_client()
        sheet = client.open_by_key(config.SPREADSHEET_ID)
        ws = sheet.worksheet(SHEET_TRANSACTIONS)
        records = ws.get_all_records()

        if not records:
            return pl.DataFrame()

        df = pl.DataFrame(records)
        return df.filter(pl.col("Date") == date_str)
    except Exception as e:
        logger.error(f"Gagal membaca transaksi harian: {e}")
        return pl.DataFrame()


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
