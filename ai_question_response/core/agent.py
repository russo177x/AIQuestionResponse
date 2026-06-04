from __future__ import annotations

from ai_question_response.core.classifier import classify_question
from ai_question_response.core.models import AnswerRequest, AnswerResult, QuestionType
from ai_question_response.core.sequence_solver import solve_sequences_in_text
from ai_question_response.services.llm import OllamaClient, OllamaUnavailableError


class QuestionAgent:
    """Orquestra regras determinísticas e Ollama obrigatório para uso autorizado."""

    def __init__(self, llm: OllamaClient | None = None) -> None:
        self.llm = llm or OllamaClient()

    def answer(self, request: AnswerRequest) -> AnswerResult:
        text = request.text.strip()
        if not text:
            return AnswerResult(
                answer="Forneça uma questão ou imagem com texto legível.",
                confidence=0,
                question_type=QuestionType.UNKNOWN,
                explanation="Entrada vazia não pode ser analisada.",
                method="input_validation",
            )

        question_type = classify_question(text)
        local_candidate = self._build_local_candidate(text, question_type)
        prompt = self._build_prompt(text, question_type, local_candidate)

        try:
            response = self.llm.generate(prompt)
        except OllamaUnavailableError as exc:
            return AnswerResult(
                answer="Ollama local obrigatório está indisponível.",
                confidence=0,
                question_type=question_type,
                explanation=str(exc),
                method="ollama_required_unavailable",
                metadata={"local_candidate": local_candidate},
            )

        confidence = 0.75 if question_type != QuestionType.BEHAVIORAL else 0.9
        if local_candidate["answer"]:
            confidence = max(confidence, local_candidate["confidence"])
        return AnswerResult(
            answer=response.text,
            confidence=min(confidence, 0.98),
            question_type=question_type,
            explanation=(
                "Resposta produzida com apoio obrigatório do Ollama local. "
                "Candidatos determinísticos, quando disponíveis, foram enviados ao modelo "
                "para validação e explicação."
            ),
            method=f"ollama_required:{response.model}",
            metadata={"local_candidate": local_candidate, "source": request.source},
        )

    def _build_local_candidate(self, text: str, question_type: QuestionType) -> dict[str, object]:
        if question_type == QuestionType.SEQUENCE:
            sequence_solutions = solve_sequences_in_text(text)
            if sequence_solutions:
                answer_lines = [str(solution.next_value) for solution in sequence_solutions]
                explanation_lines = [
                    f"Item {index + 1}: {solution.rule}. Próximo valor: {solution.next_value}."
                    for index, solution in enumerate(sequence_solutions)
                ]
                return {
                    "answer": "; ".join(answer_lines),
                    "confidence": min(solution.confidence for solution in sequence_solutions),
                    "explanation": "\n".join(explanation_lines),
                    "method": "deterministic_sequence_solver",
                }

        if question_type == QuestionType.BEHAVIORAL:
            return {
                "answer": (
                    "Sem gabarito único: responda de forma honesta e consistente "
                    "com sua experiência."
                ),
                "confidence": 0.9,
                "explanation": (
                    "Questões comportamentais medem preferências e estilo de trabalho. "
                    "Explique a dimensão avaliada e ajude o usuário a refletir, sem "
                    "fabricar uma resposta."
                ),
                "method": "ethical_behavioral_guidance",
            }

        return {"answer": "", "confidence": 0.0, "explanation": "", "method": "none"}

    def _build_prompt(
        self,
        text: str,
        question_type: QuestionType,
        local_candidate: dict[str, object],
    ) -> str:
        return (
            "Você é um tutor local de estudos. Use apenas para documentos próprios, "
            "simulados autorizados e treino. Nunca automatize fraude em avaliações.\n"
            "Responda em português. Seja objetivo, mas inclua a regra/raciocínio.\n"
            "Para questões comportamentais, não fabrique gabarito; explique a dimensão "
            "avaliada e oriente resposta honesta.\n"
            "Se houver candidato determinístico, valide-o antes de responder.\n\n"
            f"Tipo provável: {question_type.value}\n"
            f"Candidato local: {local_candidate}\n\n"
            f"Questão:\n{text}\n\n"
            "Formato esperado:\n"
            "Resposta: ...\n"
            "Confiança: alta/média/baixa\n"
            "Explicação: ..."
        )
