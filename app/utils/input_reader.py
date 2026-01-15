from typing import Optional, Tuple

from fastapi import UploadFile

from app.security.exceptions import UploadValidationError
from app.security.upload_guard import extract_text_from_upload, validate_text_input


async def extract_text_from_input(
    file: Optional[UploadFile],
    text_input: Optional[str],
) -> Tuple[str, Optional[str]]:
    if file and file.filename:
        content, filename = await extract_text_from_upload(file)
        return content, filename

    if text_input:
        return validate_text_input(text_input), None

    raise UploadValidationError("Envie um arquivo ou cole o texto.")
