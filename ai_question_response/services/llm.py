from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class OllamaUnavailableError(RuntimeError):
    """Erro levantado quando o Ollama obrigatório não está acessível."""


@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str


class OllamaClient:
    """Cliente obrigatório para LLM local via Ollama, sem depender de serviços externos."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 45,
    ) -> None:
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL") or "http://localhost:11434"
        ).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL") or "qwen2.5:14b-instruct-q4_K_M"
        self.timeout = timeout

    def is_available(self) -> bool:
        request = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=2) as response:
                return 200 <= response.status < 300
        except (OSError, urllib.error.URLError):
            return False

    def require_available(self) -> None:
        if not self.is_available():
            raise OllamaUnavailableError(
                "Ollama obrigatório indisponível. Inicie o Ollama, baixe o modelo configurado "
                "e confira OLLAMA_BASE_URL/OLLAMA_MODEL."
            )

    def generate(self, prompt: str) -> LLMResponse:
        self.require_available()
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.1, "num_ctx": 4096},
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise OllamaUnavailableError(f"Falha ao chamar o Ollama obrigatório: {exc}") from exc
        text = str(response_data.get("response", "")).strip()
        if not text:
            raise OllamaUnavailableError("Ollama respondeu vazio para o prompt enviado.")
        return LLMResponse(text=text, model=self.model)
