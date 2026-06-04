from ai_question_response.core.agent import QuestionAgent
from ai_question_response.core.models import AnswerRequest, QuestionType
from ai_question_response.services.llm import LLMResponse, OllamaUnavailableError


class FakeOllama:
    model = "fake-model"

    def generate(self, prompt: str) -> LLMResponse:
        if "13" in prompt:
            return LLMResponse(
                text="Resposta: 13\nConfiança: alta\nExplicação: sequência de Fibonacci.",
                model=self.model,
            )
        return LLMResponse(
            text=(
                "Resposta: sem gabarito único.\n"
                "Confiança: alta\n"
                "Explicação: responda de forma honesta."
            ),
            model=self.model,
        )


class UnavailableOllama:
    def generate(self, prompt: str) -> LLMResponse:
        raise OllamaUnavailableError("Ollama não está rodando")


def test_agent_requires_ollama_and_uses_local_sequence_candidate() -> None:
    agent = QuestionAgent(llm=FakeOllama())  # type: ignore[arg-type]
    result = agent.answer(AnswerRequest(text="Complete: 1, 1, 2, 3, 5, 8, ___."))
    assert "13" in result.answer
    assert result.question_type == QuestionType.SEQUENCE
    assert result.method == "ollama_required:fake-model"
    assert result.metadata["local_candidate"]["answer"] == "13"


def test_agent_guides_behavioral_questions_with_ollama() -> None:
    agent = QuestionAgent(llm=FakeOllama())  # type: ignore[arg-type]
    result = agent.answer(AnswerRequest(text="Teste comportamental: como você lida com feedback?"))
    assert result.question_type == QuestionType.BEHAVIORAL
    assert result.method == "ollama_required:fake-model"
    assert "honesta" in result.answer


def test_agent_reports_required_ollama_when_unavailable() -> None:
    agent = QuestionAgent(llm=UnavailableOllama())  # type: ignore[arg-type]
    result = agent.answer(AnswerRequest(text="Complete: 1, 3, 5, 7, ___."))
    assert result.confidence == 0
    assert result.method == "ollama_required_unavailable"
    assert "indisponível" in result.answer
