from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class QuestionType(StrEnum):
    SEQUENCE = "sequencia"
    MATH = "matematica"
    INFERENCE = "inferencia"
    BEHAVIORAL = "comportamental"
    UNKNOWN = "desconhecido"


@dataclass
class AnswerRequest:
    text: str
    source: str = "manual"


@dataclass
class AnswerResult:
    answer: str
    confidence: float
    question_type: QuestionType
    explanation: str
    method: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OCRResult:
    text: str
    source: str
    confidence: float | None = None


@dataclass
class DatasetQuestion:
    id: str
    category: QuestionType
    prompt: str
    expected_answer: str | None = None
    explanation: str = ""
    options: list[str] = field(default_factory=list)

    @classmethod
    def model_validate(cls, item: dict[str, Any]) -> DatasetQuestion:
        return cls(
            id=str(item["id"]),
            category=QuestionType(item["category"]),
            prompt=str(item["prompt"]),
            expected_answer=item.get("expected_answer"),
            explanation=str(item.get("explanation", "")),
            options=list(item.get("options", [])),
        )
