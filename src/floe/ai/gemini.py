import logging
from datetime import datetime
from typing import cast

from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import (
    after_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from floe import config
from floe.models import VALID_CATEGORIES, Transaction, TransactionSource, TransactionType

logger = logging.getLogger(__name__)

client = genai.Client(api_key=config.GEMINI_API_KEY.get_secret_value())


class GeminiOutput(BaseModel):
    success: bool
    date: str = ""
    amount: int = 0
    type: TransactionType = TransactionType.PENGELUARAN
    category: str = ""
    description: str = ""
    note: str = ""
    reason: str = ""


def _system_instruction() -> str:
    return f"""
Kamu adalah asisten keuangan pribadi bernama Floe.
Tugasmu HANYA mengekstrak informasi transaksi keuangan dari pesan atau gambar pengguna.
Hari ini: {datetime.now().strftime("%d/%m/%Y")}.

SELALU balas dalam format JSON yang valid. Tidak ada teks lain di luar JSON.

Format JSON yang harus kamu kembalikan:
{{
  "success": true,
  "date": "dd/mm/yyyy",
  "amount": 35000,
  "type": "pengeluaran",
  "category": "makan & minum",
  "description": "Makan siang nasi padang",
  "note": "pesan asli user"
}}

Jika pesan tidak mengandung transaksi keuangan apapun:
{{
  "success": false,
  "reason": "Pesan tidak mengandung transaksi"
}}

Aturan penting:
- "amount" selalu berupa bilangan bulat positif (Rupiah). Konversi "35rb" -> 35000, "1.5jt" -> 1500000.
- "type" hanya boleh: "pengeluaran" atau "pemasukan"
- "category" harus salah satu dari: {", ".join(VALID_CATEGORIES)}
- "date" adalah tanggal transaksi (bukan hari ini jika disebutkan berbeda). Default hari ini.
- "note" adalah pesan asli dari pengguna, salin apa adanya.
- Untuk gambar: ekstrak info dari struk atau screenshot transfer.
- Jika gambar buram atau tidak terbaca, kembalikan success: false.
""".strip()


def parse_text(message: str) -> Transaction | None:
    try:
        return _call_gemini(message, source=TransactionSource.TEXT, note=message)
    except Exception as e:
        logger.error("Gemini gagal setelah semua retry: %s", e)
        return None


def parse_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Transaction | None:
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    prompt = "Ekstrak informasi transaksi dari gambar berikut:"
    try:
        return _call_gemini([prompt, image_part], source=TransactionSource.PHOTO, note="[foto]")
    except Exception as e:
        logger.error("Gemini gagal setelah semua retry: %s", e)
        return None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=8),
    after=after_log(logger, logging.WARNING),
)
def _call_gemini(
    prompt: str | list,
    source: TransactionSource,
    note: str,
) -> Transaction | None:
    response = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=_system_instruction(),
            response_mime_type="application/json",
            response_schema=GeminiOutput,
        ),
    )

    output = cast(GeminiOutput | None, response.parsed)
    if output is None:
        if response.candidates:
            finish_reason = response.candidates[0].finish_reason
            reason = finish_reason.name if finish_reason else "UNKNOWN"
        else:
            reason = "UNKNOWN"
        logger.error(
            f"Gemini response tidak sesuai schema: finish_reason={reason}, text={response.text}"
        )
        return None

    if not output.success:
        logger.info(f"Bukan transaksi: {output.reason}")
        return None

    return Transaction(
        date=output.date or datetime.now().strftime("%d/%m/%Y"),
        amount=output.amount,
        type=output.type,
        category=output.category or "lainnya",
        description=output.description,
        source=source,
        note=note,
    )
