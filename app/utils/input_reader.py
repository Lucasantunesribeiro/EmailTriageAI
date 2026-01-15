from typing import Optional, Tuple

from fastapi import UploadFile

from app.config import settings
from app.utils.pdf_reader import read_pdf


async def extract_text_from_input(
    file: Optional[UploadFile],
    text_input: Optional[str],
) -> Tuple[str, Optional[str]]:
    if file and file.filename:
        filename = file.filename.lower()
        if not (filename.endswith(".txt") or filename.endswith(".pdf")):
            raise ValueError("Tipo de arquivo invalido. Use .txt ou .pdf")
        file_bytes = await file.read()
        if len(file_bytes) > settings.max_file_bytes:
            raise ValueError("Arquivo maior que 2MB")
        if filename.endswith(".pdf"):
            content = read_pdf(file_bytes)
        else:
            content = file_bytes.decode("utf-8", errors="ignore")
        return content, filename

    if text_input:
        return text_input, None

    raise ValueError("Envie um arquivo ou cole o texto")
