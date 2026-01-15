import re
from typing import Dict, List

import nltk
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer

SIGNATURE_MARKERS = (
    "atenciosamente",
    "att",
    "abracos",
    "obrigado",
    "obrigada",
    "abs",
)

REPLY_MARKERS = (
    "-----original message-----",
    "de:",
    "from:",
    "enviado:",
    "sent:",
    "assunto:",
    "subject:",
)


def _ensure_nltk() -> None:
    try:
        stopwords.words("portuguese")
    except LookupError:
        nltk.download("stopwords", quiet=True)
    try:
        RSLPStemmer()
    except LookupError:
        nltk.download("rslp", quiet=True)


def _strip_noise_lines(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned: List[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith(">"):
            continue
        if any(marker in lower for marker in REPLY_MARKERS):
            break
        if any(lower.startswith(marker) for marker in SIGNATURE_MARKERS):
            break
        cleaned.append(stripped)
    return "\n".join(cleaned)


def preprocess_text(text: str) -> Dict[str, object]:
    _ensure_nltk()
    original = text.strip()
    cleaned_lines = _strip_noise_lines(original)
    normalized = re.sub(r"\s+", " ", cleaned_lines.lower()).strip()
    tokens = re.findall(r"[a-zA-Z0-9]+", normalized)
    stop_words = set(stopwords.words("portuguese"))
    stemmer = RSLPStemmer()
    filtered = [token for token in tokens if token not in stop_words]
    stemmed = [stemmer.stem(token) for token in filtered]
    clean_text = " ".join(stemmed)
    stats = {
        "num_chars": len(original),
        "num_words": len(tokens),
    }
    return {"clean_text": clean_text, "tokens": stemmed, "stats": stats}
