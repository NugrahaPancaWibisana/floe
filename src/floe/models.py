from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class TransactionType(StrEnum):
    PENGELUARAN = "pengeluaran"
    PEMASUKAN = "pemasukan"


class TransactionSource(StrEnum):
    TEXT = "text"
    PHOTO = "photo"


VALID_CATEGORIES = [
    "makan & minum",
    "transport",
    "belanja",
    "hiburan",
    "kesehatan",
    "tagihan",
    "gaji",
    "freelance",
    "investasi",
    "transfer",
    "lainnya",
]


@dataclass
class Transaction:
    amount: int
    type: TransactionType
    category: str
    description: str
    source: TransactionSource
    user_id: int = 0
    date: str = field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    note: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_row(self) -> list[str | int]:
        return [
            self.date,
            self.amount,
            self.type.value,
            self.category,
            self.description,
            self.source.value,
            self.note,
            self.timestamp,
            self.user_id,
        ]

    def format_summary_line(self) -> str:
        sign = "+" if self.type == TransactionType.PEMASUKAN else "-"
        return f"{sign} *{self.description}*\n   Rp {self.amount:,} . {self.category} . {self.date}"
