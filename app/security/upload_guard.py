import re
from pathlib import Path
from typing import Tuple

import anyio
from fastapi import UploadFile

from app.security.exceptions import PayloadTooLargeError, UploadValidationError
from app.security.limits import (
    ALLOWED_EXTENSIONS,
    MAX_EXTRACTED_CHARS,
    MAX_FILE_BYTES,
    MAX_PDF_PAGES,
    MAX_TEXT_CHARS,
    PDF_TIMEOUT_SECONDS,
)
from app.utils.pdf_reader import read_pdf

SUSPICIOUS_SUFFIXES = {
    ".exe",
    ".js",
    ".bat",
    ".cmd",
    ".sh",
    ".ps1",
    ".php",
    ".py",
    ".com",
    ".scr",
}
TEXT_PRINTABLE_RATIO = 0.9


def _normalize_filename(filename: str) -> str:
    if not filename or "\x00" in filename:
        raise UploadValidationError("Nome de arquivo invalido.")
    name = Path(filename).name
    if name != filename or ".." in filename:
        raise UploadValidationError("Nome de arquivo invalido.")
    suffixes = [suffix.lower() for suffix in Path(name).suffixes]
    if not suffixes:
        raise UploadValidationError("Arquivo sem extensao.")
    if suffixes[-1] not in ALLOWED_EXTENSIONS:
        raise UploadValidationError("Tipo de arquivo invalido. Use .txt ou .pdf")
    if any(suffix in SUSPICIOUS_SUFFIXES for suffix in suffixes[:-1]):
        raise UploadValidationError("Extensao suspeita no arquivo.")
    return name


def _is_pdf_magic(file_bytes: bytes) -> bool:
    head = file_bytes[:1024].lstrip()
    return head.startswith(b"%PDF-")


def _decode_text(file_bytes: bytes) -> str:
    if b"\x00" in file_bytes:
        raise UploadValidationError("Arquivo de texto invalido.")
    last_error = None
    for encoding in ("utf-8", "latin-1"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
            text = ""
    if not text:
        raise UploadValidationError("Arquivo de texto invalido.") from last_error
    printable = sum(ch.isprintable() or ch in "\n\r\t" for ch in text)
    ratio = printable / max(1, len(text))
    if ratio < TEXT_PRINTABLE_RATIO:
        raise UploadValidationError("Arquivo de texto invalido.")
    return text


def validate_text_input(text_input: str) -> str:
    cleaned = text_input.strip()
    if not cleaned:
        raise UploadValidationError("Conteudo vazio.")
    if len(cleaned) > MAX_TEXT_CHARS:
        raise UploadValidationError("Texto maior que o limite permitido.")
    return cleaned


async def _read_upload_bytes(file: UploadFile) -> bytes:
    buffer = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > MAX_FILE_BYTES:
            raise PayloadTooLargeError("Arquivo maior que o limite permitido.")
    return bytes(buffer)


async def _read_pdf_with_timeout(file_bytes: bytes) -> str:
    async with anyio.fail_after(PDF_TIMEOUT_SECONDS):
        return await anyio.to_thread.run_sync(read_pdf, file_bytes, MAX_PDF_PAGES)


async def extract_text_from_upload(file: UploadFile) -> Tuple[str, str]:
    filename = _normalize_filename(file.filename or "")
    file_bytes = await _read_upload_bytes(file)

    if filename.lower().endswith(".pdf"):
        if not _is_pdf_magic(file_bytes):
            raise UploadValidationError("PDF invalido.")
        try:
            text = await _read_pdf_with_timeout(file_bytes)
        except TimeoutError as exc:
            raise UploadValidationError("Tempo excedido ao ler PDF.") from exc
        except Exception as exc:  # noqa: BLE001
            raise UploadValidationError("PDF invalido.") from exc
    else:
        if _is_pdf_magic(file_bytes):
            raise UploadValidationError("Arquivo parece PDF, mas extensao nao confere.")
        text = _decode_text(file_bytes)

    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        raise UploadValidationError("Conteudo vazio.")
    if len(text) > MAX_EXTRACTED_CHARS:
        raise UploadValidationError("Texto maior que o limite permitido.")
    return text, filename
