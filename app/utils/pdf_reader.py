from io import BytesIO

from PyPDF2 import PdfReader


def read_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("PDF invalido") from exc
