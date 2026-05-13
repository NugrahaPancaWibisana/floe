import pytest
from pydantic import ValidationError

from floe.models import Transaction, TransactionSource, TransactionType


def test_transaction_to_row_preserves_sheet_order() -> None:
    tx = Transaction(
        amount=35000,
        type=TransactionType.PENGELUARAN,
        category="makan & minum",
        description="Makan siang",
        source=TransactionSource.TEXT,
        date="12/05/2026",
        note="Makan siang 35rb",
        timestamp="2026-05-12T09:30:00",
    )

    assert tx.to_row() == [
        "12/05/2026",
        35000,
        "pengeluaran",
        "makan & minum",
        "Makan siang",
        "text",
        "Makan siang 35rb",
        "2026-05-12T09:30:00",
    ]


@pytest.mark.parametrize(
    ("tx_type", "expected_prefix"),
    [
        (TransactionType.PENGELUARAN, "-"),
        (TransactionType.PEMASUKAN, "+"),
    ],
)
def test_transaction_format_summary_line_sign(
    tx_type: TransactionType, expected_prefix: str
) -> None:
    tx = Transaction(
        amount=12500,
        type=tx_type,
        category="transport",
        description="Bus",
        source=TransactionSource.TEXT,
        date="12/05/2026",
    )

    assert tx.format_summary_line().startswith(f"{expected_prefix} *Bus*")
    assert "Rp 12,500" in tx.format_summary_line()


def test_transaction_rejects_invalid_enum_values() -> None:
    with pytest.raises(ValidationError):
        Transaction(
            amount=1000,
            type="invalid",
            category="lainnya",
            description="Invalid",
            source="text",
        )
