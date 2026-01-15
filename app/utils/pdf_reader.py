from io import BytesIO

from PyPDF2 import PdfReader


def read_pdf(file_bytes: bytes, max_pages: int) -> str:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        if reader.is_encrypted:
            raise ValueError("PDF protegido")
        if len(reader.pages) > max_pages:
            raise ValueError("PDF acima do limite de paginas")
        pages = []
        for page in reader.pages[:max_pages]:
            pages.append(page.extract_text() or "")
        return "\n".join(pages).strip()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("PDF invalido") from exc
