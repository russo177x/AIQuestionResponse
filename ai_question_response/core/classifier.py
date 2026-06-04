from __future__ import annotations

import re

from ai_question_response.core.models import QuestionType

_SEQUENCE_HINTS = (
    "sequência",
    "sequencia",
    "próximo elemento",
    "proximo elemento",
    "complete",
    "descubra a lógica",
    "descubra a logica",
)
_BEHAVIORAL_HINTS = (
    "estilo de trabalho",
    "perfil",
    "comportamental",
    "situação no trabalho",
    "situacao no trabalho",
    "colega",
    "gestor",
    "equipe",
)
_INFERENCE_HINTS = (
    "infere",
    "inferência",
    "inferencia",
    "conclui",
    "premissa",
    "argumento",
    "necessariamente",
    "texto",
)
_MATH_HINTS = (
    "calcule",
    "quanto é",
    "quanto e",
    "porcentagem",
    "regra de três",
    "regra de tres",
    "probabilidade",
)


def classify_question(text: str) -> QuestionType:
    """Classifica rapidamente uma questão por palavras-chave e estrutura."""
    normalized = text.casefold()
    if any(hint in normalized for hint in _SEQUENCE_HINTS):
        return QuestionType.SEQUENCE
    if any(hint in normalized for hint in _BEHAVIORAL_HINTS):
        return QuestionType.BEHAVIORAL
    if any(hint in normalized for hint in _INFERENCE_HINTS):
        return QuestionType.INFERENCE
    if any(hint in normalized for hint in _MATH_HINTS):
        return QuestionType.MATH
    if re.search(r"(-?\d+\s*,\s*){2,}-?\d+", text):
        return QuestionType.SEQUENCE
    if re.search(r"\d+\s*[%+\-*/x×÷]", text):
        return QuestionType.MATH
    return QuestionType.UNKNOWN
