from __future__ import annotations

import polars as pl

from floe.sheets import client as sheets


class _BudgetWorksheet:
    def __init__(self, records: list[dict[str, object]]) -> None:
        self.records = records
        self.updated: list[tuple[str, list[list[int]]]] = []
        self.appended: list[list[object]] = []

    def get_all_records(self) -> list[dict[str, object]]:
        return self.records

    def update(self, *, values: list[list[int]], range_name: str, value_input_option) -> None:
        self.updated.append((range_name, values))

    def append_row(self, row: list[object], value_input_option) -> None:
        self.appended.append(row)


def test_compute_summary_empty_dataframe() -> None:
    assert sheets.compute_summary(pl.DataFrame()) == {
        "total_in": 0,
        "total_out": 0,
        "net": 0,
        "by_category": {},
    }


def test_compute_summary_totals_and_groups_expenses() -> None:
    df = pl.DataFrame(
        {
            "Amount": ["10000", "25000", "50000", "bad"],
            "Type": ["pengeluaran", "pengeluaran", "pemasukan", "pengeluaran"],
            "Category": ["transport", "makan & minum", "gaji", "transport"],
        }
    )

    assert sheets.compute_summary(df) == {
        "total_in": 50000,
        "total_out": 35000,
        "net": 15000,
        "by_category": {"makan & minum": 25000, "transport": 10000},
    }


def test_compute_summary_missing_required_columns_returns_empty_summary() -> None:
    assert sheets.compute_summary(pl.DataFrame({"Amount": [1000]})) == {
        "total_in": 0,
        "total_out": 0,
        "net": 0,
        "by_category": {},
    }


def test_set_budget_updates_existing_budget(monkeypatch) -> None:
    worksheet = _BudgetWorksheet(
        [{"UserID": 42, "Category": "transport", "Limit": 50000}],
    )
    monkeypatch.setattr(sheets, "_ensure_budgets_tab", lambda: worksheet)

    sheets.set_budget(user_id=42, category="transport", limit=75000)

    assert worksheet.updated == [("C2", [[75000]])]
    assert worksheet.appended == []


def test_set_budget_appends_new_budget(monkeypatch) -> None:
    worksheet = _BudgetWorksheet([])
    monkeypatch.setattr(sheets, "_ensure_budgets_tab", lambda: worksheet)

    sheets.set_budget(user_id=42, category="makan & minum", limit=100000)

    assert worksheet.updated == []
    assert worksheet.appended == [[42, "makan & minum", 100000]]


def test_get_budgets_filters_current_user(monkeypatch) -> None:
    worksheet = _BudgetWorksheet(
        [
            {"UserID": 42, "Category": "transport", "Limit": "50000"},
            {"UserID": 13, "Category": "hiburan", "Limit": "25000"},
        ]
    )
    monkeypatch.setattr(sheets, "_ensure_budgets_tab", lambda: worksheet)

    assert sheets.get_budgets(user_id=42) == {"transport": 50000}


def test_check_budget_alert_returns_message_when_spending_exceeds_limit(monkeypatch) -> None:
    monkeypatch.setattr(sheets, "get_budgets", lambda user_id: {"transport": 50000})
    monkeypatch.setattr(
        sheets,
        "get_transactions_this_month",
        lambda user_id: pl.DataFrame(
            {
                "Amount": [30000, 25000, 90000],
                "Type": ["pengeluaran", "pengeluaran", "pemasukan"],
                "Category": ["transport", "transport", "gaji"],
            }
        ),
    )

    message = sheets.check_budget_alert(user_id=42, category="transport")

    assert message is not None
    assert "transport" in message
    assert "Rp 50,000" in message
    assert "Rp 55,000" in message


def test_check_budget_alert_returns_none_when_category_has_no_budget(monkeypatch) -> None:
    monkeypatch.setattr(sheets, "get_budgets", lambda user_id: {})

    assert sheets.check_budget_alert(user_id=42, category="transport") is None
