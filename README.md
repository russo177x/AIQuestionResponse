# AIQuestionResponse

MVP de agente **local e autorizado** para leitura, OCR e interpretação de questionários próprios, documentos pessoais, simulados de estudo e materiais em que você tem permissão de uso.

> Importante: o projeto não deve ser usado para burlar avaliações, processos seletivos, provas ou plataformas de terceiros. Para testes comportamentais, o agente orienta dimensões avaliadas e recomenda respostas honestas, sem fabricar gabaritos.

## Viabilidade no hardware informado

Configuração informada: RTX 5070 Ti, 32 GB de RAM e Ryzen 5800X.

Esse hardware é adequado para o MVP local com OCR, captura de tela e Ollama obrigatório. Para baixa latência, a rota recomendada é usar modelos quantizados 7B a 14B:

- primeira opção: `qwen2.5:14b-instruct-q4_K_M`, se couber confortavelmente na VRAM;
- opção mais rápida: um modelo 7B/8B quantizado;
- manter temperatura baixa (`0.1`) e contexto moderado para reduzir alucinação.

## Arquitetura

```text
Tela local autorizada ou upload de imagem
        ↓
OCR local com Tesseract
        ↓
Classificação da questão
        ↓
Candidato determinístico para sequências, quando aplicável
        ↓
Ollama local obrigatório valida, explica e responde
        ↓
Resposta com explicação, método, confiança e metadados
```

## Funcionalidades do MVP

- Interface web local rápida em `http://127.0.0.1:8000`.
- Endpoint para responder texto colado manualmente.
- Endpoint para upload de imagem com OCR.
- Endpoint para capturar a tela local autorizada e tentar responder.
- Endpoint `/health/ollama` para validar se o Ollama obrigatório está acessível.
- Solver determinístico para padrões comuns, enviado ao Ollama como candidato:
  - progressão aritmética;
  - progressão geométrica;
  - Fibonacci;
  - quadrados perfeitos;
  - diferenças de segunda ordem;
  - padrão linguístico em português: `2, 10, 12, 16, 17, 18, 19 -> 200`.
- Dataset sintético com 40 questões de treino: 10 de lógica/sequência, 10 de matemática, 10 de inferência e 10 comportamentais.

## Instalação rápida

Para Windows, você pode usar o instalador automático [`scripts/Install-Windows.ps1`](scripts/Install-Windows.ps1). Consulte também o passo a passo completo e a lista de comandos em [`COMMANDS.md`](COMMANDS.md).

Resumo:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
ollama pull qwen2.5:14b-instruct-q4_K_M
python -m ai_question_response
```

No Windows, use PowerShell. Para instalar fora do disco do sistema, informe `-InstallRoot`, por exemplo `D:\AIQuestionResponse`.

## Ollama é obrigatório

A aplicação não responde em modo apenas determinístico. O solver local pode gerar candidatos, mas o Ollama é sempre chamado para ajudar a validar, explicar e responder.

Variáveis úteis:

```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=qwen2.5:14b-instruct-q4_K_M
```

No PowerShell:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"
```

## Execução

```bash
python -m ai_question_response
```

Abra:

```text
http://127.0.0.1:8000
```

## Endpoints principais

### `GET /health/ollama`

Confirma se o Ollama está acessível e mostra o modelo configurado.

### `POST /answer`

```json
{
  "text": "Complete: 1, 3, 5, 7, ___.",
  "source": "manual"
}
```

### `POST /ocr/answer`

Recebe um arquivo de imagem em `multipart/form-data` no campo `file`.

### `POST /capture/answer`

Captura a tela local do computador em que o servidor está rodando, aplica OCR e tenta responder. Use somente em documentos próprios e contextos autorizados.

### `GET /dataset`

Retorna o dataset sintético de treino.

## Testes e formatação

```bash
pytest
ruff check .
```
