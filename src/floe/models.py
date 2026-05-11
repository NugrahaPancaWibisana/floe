from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


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


class Transaction(BaseModel):
    amount: int
    type: TransactionType
    category: str
    description: str
    source: TransactionSource
    date: str = Field(default_factory=lambda: datetime.now().strftime("%d/%m/%Y"))
    note: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

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
        ]

    def format_summary_line(self) -> str:
        sign = "+" if self.type == TransactionType.PEMASUKAN else "-"
        return f"{sign} *{self.description}*\n   Rp {self.amount:,} . {self.category} . {self.date}"
