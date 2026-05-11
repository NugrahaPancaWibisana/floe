"""
Test parsing Gemini. Jalankan dengan: uv run pytest tests/ -v

PERHATIAN: Test ini melakukan real API call ke Gemini.
Butuh GEMINI_API_KEY di .env.
"""

import pytest
from floe.ai.gemini import parse_text
from floe.models import TransactionType


def test_parse_pengeluaran_sederhana():
    tx = parse_text("Makan siang 35rb")
    assert tx is not None
    assert tx.amount == 35000
    assert tx.type == TransactionType.PENGELUARAN


def test_parse_pemasukan():
    tx = parse_text("Gaji bulan ini masuk 5 juta")
    assert tx is not None
    assert tx.amount == 5_000_000
    assert tx.type == TransactionType.PEMASUKAN


def test_parse_bukan_transaksi():
    tx = parse_text("Halo, apa kabar?")
    assert tx is None


def test_parse_nominal_berbagai_format():
    cases = [
        ("Beli kopi 15.000", 15000),
        ("Bensin 50rb", 50000),
        ("Transfer 1.5jt", 1_500_000),
        ("Bayar 250000", 250000),
    ]
    for pesan, expected in cases:
        tx = parse_text(pesan)
        assert tx is not None, f"Gagal parse: {pesan}"
        assert tx.amount == expected, f"Amount salah untuk: {pesan}"
