from __future__ import annotations

import io

import pytesseract
from PIL import Image, ImageOps

from ai_question_response.core.models import OCRResult


def image_bytes_to_text(data: bytes, source: str = "upload") -> OCRResult:
    image = Image.open(io.BytesIO(data))
    normalized = ImageOps.grayscale(image)
    text = pytesseract.image_to_string(normalized, lang="por+eng")
    return OCRResult(text=text.strip(), source=source)
