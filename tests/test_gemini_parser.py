from floe.ai import gemini
from floe.ai.gemini import GeminiOutput, parse_text
from floe.models import TransactionType


class _GeminiResponse:
    def __init__(self, output: GeminiOutput) -> None:
        self.parsed = output
        self.candidates = []
        self.text = ""


def _mock_gemini(monkeypatch, outputs: dict[str, GeminiOutput]) -> None:
    def generate_content(*, contents, **_kwargs):
        return _GeminiResponse(outputs[contents])

    monkeypatch.setattr(gemini.client.models, "generate_content", generate_content)


def _output(amount: int, tx_type: str = "pengeluaran") -> GeminiOutput:
    return GeminiOutput(
        success=True,
        date="12/05/2026",
        amount=amount,
        type=tx_type,
        category="makan & minum",
        description="Makan siang",
        note="",
    )


def test_parse_pengeluaran_sederhana(monkeypatch):
    _mock_gemini(monkeypatch, {"Makan siang 35rb": _output(35000)})

    tx = parse_text("Makan siang 35rb")

    assert tx is not None
    assert tx.amount == 35000
    assert tx.type == TransactionType.PENGELUARAN


def test_parse_pemasukan(monkeypatch):
    _mock_gemini(
        monkeypatch,
        {"Gaji bulan ini masuk 5 juta": _output(5_000_000, tx_type="pemasukan")},
    )

    tx = parse_text("Gaji bulan ini masuk 5 juta")

    assert tx is not None
    assert tx.amount == 5_000_000
    assert tx.type == TransactionType.PEMASUKAN


def test_parse_bukan_transaksi(monkeypatch):
    _mock_gemini(
        monkeypatch,
        {
            "Halo, apa kabar?": GeminiOutput(
                success=False, reason="Pesan tidak mengandung transaksi"
            )
        },
    )

    tx = parse_text("Halo, apa kabar?")

    assert tx is None


def test_parse_nominal_berbagai_format(monkeypatch):
    cases = [
        ("Beli kopi 15.000", 15000),
        ("Bensin 50rb", 50000),
        ("Transfer 1.5jt", 1_500_000),
        ("Bayar 250000", 250000),
    ]
    _mock_gemini(monkeypatch, {pesan: _output(expected) for pesan, expected in cases})

    for pesan, expected in cases:
        tx = parse_text(pesan)
        assert tx is not None, f"Gagal parse: {pesan}"
        assert tx.amount == expected, f"Amount salah untuk: {pesan}"
