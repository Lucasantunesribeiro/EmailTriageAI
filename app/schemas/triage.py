from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EmailTriageResult(BaseModel):
    category: Literal["Produtivo", "Improdutivo"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary: str = Field(max_length=200)
    suggested_reply: str = Field(max_length=700)
    tags: List[str] = Field(min_length=3, max_length=8)
    needs_human_review: bool
    reasons: List[str] = Field(min_length=2, max_length=5)

    @field_validator("summary")
    @classmethod
    def normalize_summary(cls, value: str) -> str:
        return value.strip()[:200]

    @field_validator("suggested_reply")
    @classmethod
    def normalize_reply(cls, value: str) -> str:
        return value.strip()[:700]

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: List[str]) -> List[str]:
        cleaned = [tag.strip().lower() for tag in value if tag.strip()]
        if not 3 <= len(cleaned) <= 8:
            raise ValueError("tags must have between 3 and 8 items")
        return cleaned

    @field_validator("reasons")
    @classmethod
    def normalize_reasons(cls, value: List[str]) -> List[str]:
        cleaned = [reason.strip() for reason in value if reason.strip()]
        if not 2 <= len(cleaned) <= 5:
            raise ValueError("reasons must have between 2 and 5 items")
        return cleaned


class TriageResponse(BaseModel):
    result: EmailTriageResult
    source: str
    email_hash: str
    stats: Dict[str, int]
    baseline_prob: Optional[float] = None
