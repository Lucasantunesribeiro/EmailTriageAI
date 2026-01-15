from app.config import settings

ALLOWED_EXTENSIONS = {".txt", ".pdf"}

MAX_BODY_BYTES = settings.max_body_bytes
MAX_FILE_BYTES = settings.max_file_bytes
MAX_TEXT_CHARS = settings.max_chars
MAX_EXTRACTED_CHARS = settings.max_extracted_chars
MAX_PDF_PAGES = settings.max_pdf_pages
PDF_TIMEOUT_SECONDS = settings.pdf_timeout_seconds
LLM_TIMEOUT_SECONDS = settings.llm_timeout_seconds

RATE_LIMIT_WINDOW_SECONDS = settings.rate_limit_window_seconds
RATE_LIMIT_ANALYZE = settings.rate_limit_analyze
RATE_LIMIT_API = settings.rate_limit_api
RATE_LIMIT_FEEDBACK = settings.rate_limit_feedback
