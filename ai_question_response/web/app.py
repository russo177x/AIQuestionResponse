from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, Response

from ai_question_response.core.agent import QuestionAgent
from ai_question_response.core.models import AnswerRequest, DatasetQuestion
from ai_question_response.services.capture import capture_screen_png
from ai_question_response.services.ocr import image_bytes_to_text

app = FastAPI(
    title="AIQuestionResponse",
    description="Agente local para documentos próprios, simulados autorizados e treino guiado.",
    version="0.2.0",
)
agent = QuestionAgent()
DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_questions.json"
ImageUpload = Annotated[UploadFile, File(...)]

HTML_PAGE = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AIQuestionResponse</title>
  <style>
    body {
      font-family: Inter, Arial, sans-serif;
      margin: 2rem;
      background: #0f172a;
      color: #e2e8f0;
    }
    main { max-width: 980px; margin: auto; }
    textarea {
      width: 100%;
      min-height: 190px;
      border-radius: 12px;
      padding: 1rem;
      font-size: 1rem;
    }
    button {
      border: 0;
      border-radius: 10px;
      padding: .8rem 1rem;
      margin: .4rem .3rem .4rem 0;
      cursor: pointer;
      background: #8b5cf6;
      color: white;
      font-weight: 700;
    }
    input { margin: .7rem 0; }
    pre {
      white-space: pre-wrap;
      background: #111827;
      padding: 1rem;
      border-radius: 12px;
      border: 1px solid #334155;
    }
    .note { color: #cbd5e1; font-size: .95rem; }
  </style>
</head>
<body>
<main>
  <h1>AIQuestionResponse</h1>
  <p class="note">
    Use apenas com documentos próprios, simulados autorizados e treino.
    O Ollama local é obrigatório para responder.
  </p>
  <textarea id="text" placeholder="Cole a questão aqui..."></textarea>
  <br />
  <button onclick="answerText()">Responder texto</button>
  <button onclick="captureAndRead()">Ler minha tela local</button>
  <input id="file" type="file" accept="image/*" onchange="uploadImage()" />
  <h2>Resultado</h2>
  <pre id="result">Aguardando...</pre>
</main>
<script>
async function answerText() {
  const text = document.getElementById('text').value;
  const res = await fetch('/answer', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text, source: 'web'})
  });
  document.getElementById('result').textContent = JSON.stringify(await res.json(), null, 2);
}
async function uploadImage() {
  const file = document.getElementById('file').files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/ocr/answer', {method: 'POST', body: form});
  const data = await res.json();
  document.getElementById('text').value = data.ocr.text;
  document.getElementById('result').textContent = JSON.stringify(data, null, 2);
}
async function captureAndRead() {
  const res = await fetch('/capture/answer', {method: 'POST'});
  const data = await res.json();
  document.getElementById('text').value = data.ocr.text;
  document.getElementById('result').textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return HTML_PAGE


@app.get("/health/ollama")
def ollama_health() -> dict[str, str | bool]:
    return {"available": agent.llm.is_available(), "model": agent.llm.model}


@app.post("/answer")
def answer(request: AnswerRequest):
    return agent.answer(request)


@app.post("/ocr/answer")
async def ocr_answer(file: ImageUpload):
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Arquivo vazio.")
    ocr = image_bytes_to_text(data, source=file.filename or "upload")
    result = agent.answer(AnswerRequest(text=ocr.text, source="ocr_upload"))
    return {"ocr": ocr, "answer": result}


@app.post("/capture")
def capture() -> Response:
    data = capture_screen_png()
    return Response(content=data, media_type="image/png")


@app.post("/capture/answer")
def capture_answer():
    data = capture_screen_png()
    ocr = image_bytes_to_text(data, source="screen")
    result = agent.answer(AnswerRequest(text=ocr.text, source="screen"))
    return {"ocr": ocr, "answer": result}


@app.get("/dataset", response_model=list[DatasetQuestion])
def dataset() -> list[DatasetQuestion]:
    return [DatasetQuestion.model_validate(item) for item in json.loads(DATASET_PATH.read_text())]
