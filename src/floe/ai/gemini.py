import json
import logging
from datetime import datetime

import google.generativeai as genai
from tenacity import (
    after_log,
    retry,
    stop_after_attempt,
    wait_exponential,
)

from floe import config
from floe.models import VALID_CATEGORIES, Transaction, TransactionSource, TransactionType

logger = logging.getLogger(__name__)

genai.configure(api_key=config.GEMINI_API_KEY)
_model = genai.GenerativeModel(config.GEMINI_MODEL)

_SYSTEM_INSTRUCTION = f"""
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
    prompt = f"Pesan dari pengguna:\n{message}"
    try:
        return _call_gemini(prompt, source=TransactionSource.TEXT, note=message)
    except Exception as e:
        logger.error("Gemini gagal setelah semua retry: %s", e)
        return None


def parse_image(image_bytes: bytes, mime_type: str = "image/jpeg") -> Transaction | None:
    image_part = {"mime_type": mime_type, "data": image_bytes}
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
    try:
        full_prompt = f"{_SYSTEM_INSTRUCTION}\n\n---\n\n"
        if isinstance(prompt, str):
            full_prompt = [full_prompt + prompt]
        else:
            full_prompt = [full_prompt + prompt[0]] + prompt[1:]

        response = _model.generate_content(full_prompt)
        raw_text = response.text.strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        data = json.loads(raw_text)

        if not data.get("success"):
            logger.info(f"Bukan transaksi: {data.get('reason', 'unknown')}")
            return None

        return Transaction(
            date=data.get("date", datetime.now().strftime("%d/%m/%Y")),
            amount=int(data["amount"]),
            type=TransactionType(data["type"]),
            category=data.get("category", "lainnya"),
            description=data["description"],
            source=source,
            note=note,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Gagal parse JSON dari Gemini: {e}\nResponse: {raw_text}")
        return None
    except Exception as e:
        logger.warning("Gemini call failed (retrying...): %s", e)
        raise
