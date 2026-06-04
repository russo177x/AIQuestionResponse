# Comandos de instalação e uso no Windows

Este documento reúne os comandos para instalar, configurar, testar e usar o AIQuestionResponse no Windows com Ollama local obrigatório.


## 0. Instalação automática recomendada

Se quiser instalar tudo com um único script, inclusive colocando ambiente virtual, cache do pip e modelos do Ollama em outro disco, execute no PowerShell a partir da raiz do repositório:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\scripts\Install-Windows.ps1 -InstallRoot "D:\AIQuestionResponse" -RunTests
```

Troque `D:\AIQuestionResponse` por uma pasta em qualquer disco com mais espaço livre. Se você não informar `-InstallRoot`, o script tenta escolher automaticamente o maior disco fixo que não seja o disco do sistema.

O script faz o seguinte:

- tenta instalar Python 3.11, Ollama e Tesseract via `winget`;
- tenta usar `--location` do `winget` para instalar aplicativos em outro disco quando o instalador permitir;
- cria o ambiente virtual Python em `InstallRoot\.venv`;
- configura `PIP_CACHE_DIR` em `InstallRoot\pip-cache`;
- configura `OLLAMA_MODELS` em `InstallRoot\ollama-models` para evitar modelos grandes no disco do sistema;
- configura `OLLAMA_MODEL` e `OLLAMA_BASE_URL`;
- instala as dependências Python;
- inicia/valida o Ollama;
- baixa o modelo obrigatório;
- cria `Start-AIQuestionResponse.ps1` dentro do `InstallRoot` para iniciar a aplicação depois;
- opcionalmente executa testes com `-RunTests`.

Exemplos úteis:

```powershell
# Instala usando o maior disco não-sistema encontrado automaticamente
.\scripts\Install-Windows.ps1

# Instala em E:\AIQuestionResponse e não baixa novamente o modelo
.\scripts\Install-Windows.ps1 -InstallRoot "E:\AIQuestionResponse" -SkipModelPull

# Usa pré-requisitos já instalados manualmente e só prepara venv/modelos/configuração
.\scripts\Install-Windows.ps1 -InstallRoot "D:\AIQuestionResponse" -SkipWingetInstall
```

> Observação: alguns instaladores do `winget` não respeitam `--location`. Quando isso acontecer, o script tenta instalar o aplicativo no local padrão, mas ainda mantém os itens mais pesados do projeto — ambiente virtual, cache do pip e modelos Ollama — no `InstallRoot` escolhido.

## 1. Pré-requisitos

Abra o **PowerShell** como usuário normal, exceto quando o instalador pedir permissão administrativa.

### 1.1 Verificar Python

```powershell
py --version
```

Se o comando não existir, instale Python 3.11 ou superior pelo site oficial ou pela Microsoft Store. Depois valide novamente:

```powershell
py -3.11 --version
```

### 1.2 Instalar Ollama

Baixe e instale o Ollama para Windows em:

```text
https://ollama.com/download/windows
```

Após instalar, confira se o comando está disponível:

```powershell
ollama --version
```

### 1.3 Baixar o modelo local recomendado

Para a RTX 5070 Ti com 32 GB de RAM, comece com o modelo abaixo:

```powershell
ollama pull qwen2.5:14b-instruct-q4_K_M
```

Se quiser priorizar velocidade, configure um modelo 7B/8B compatível que você já tenha baixado no Ollama.

### 1.4 Garantir que o Ollama está rodando

Em muitos ambientes Windows, o Ollama inicia automaticamente. Para testar:

```powershell
ollama list
```

Se precisar iniciar manualmente em outro terminal:

```powershell
ollama serve
```

## 2. Instalar Tesseract OCR no Windows

O OCR depende do Tesseract. Instale uma versão Windows e marque a opção de idioma português quando disponível.

Após instalar, valide:

```powershell
tesseract --version
```

Se o comando não for reconhecido, adicione a pasta do Tesseract ao `PATH`. Um caminho comum é:

```text
C:\Program Files\Tesseract-OCR
```

Feche e reabra o PowerShell depois de alterar o `PATH`.

## 3. Preparar o projeto

Entre na pasta do repositório:

```powershell
cd C:\caminho\para\AIQuestionResponse
```

Crie o ambiente virtual:

```powershell
py -3.11 -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear scripts locais, libere apenas para o usuário atual:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois ative novamente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Atualize o `pip`:

```powershell
python -m pip install --upgrade pip
```

Instale a aplicação com dependências de desenvolvimento:

```powershell
python -m pip install -e ".[dev]"
```

## 4. Configurar o modelo obrigatório

Configure as variáveis no PowerShell atual:

```powershell
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "qwen2.5:14b-instruct-q4_K_M"
```

Valide se o Ollama responde:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

## 5. Rodar a aplicação

Se você usou o instalador automático, execute o atalho criado no `InstallRoot`:

```powershell
& "D:\AIQuestionResponse\Start-AIQuestionResponse.ps1"
```

Se você instalou manualmente, com o ambiente virtual ativo:

```powershell
python -m ai_question_response
```

Abra no navegador:

```text
http://127.0.0.1:8000
```

## 6. Testar pela API no PowerShell

### 6.1 Verificar saúde do Ollama

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health/ollama
```

### 6.2 Enviar uma questão de sequência

```powershell
$body = @{
  text = "Complete: 1, 3, 5, 7, ___."
  source = "manual"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/answer `
  -Method Post `
  -ContentType "application/json" `
  -Body $body
```

### 6.3 Enviar imagem para OCR e resposta

Troque o caminho abaixo por uma imagem sua:

```powershell
curl.exe -X POST `
  -F "file=@C:\caminho\para\questao.png" `
  http://127.0.0.1:8000/ocr/answer
```

### 6.4 Capturar tela local e responder

Use apenas com documentos próprios e contextos autorizados:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/capture/answer `
  -Method Post
```

### 6.5 Consultar dataset de treino

```powershell
Invoke-RestMethod http://127.0.0.1:8000/dataset
```

## 7. Rodar testes e formatação

Com o ambiente virtual ativo:

```powershell
python -m pytest
```

```powershell
python -m ruff check .
```

## 8. Comandos úteis de manutenção

Listar modelos baixados no Ollama:

```powershell
ollama list
```

Baixar novamente o modelo configurado:

```powershell
ollama pull qwen2.5:14b-instruct-q4_K_M
```

Trocar modelo temporariamente:

```powershell
$env:OLLAMA_MODEL = "nome-do-modelo-baixado"
```

Desativar o ambiente virtual:

```powershell
deactivate
```

## 9. Solução de problemas

### Erro: Ollama local obrigatório está indisponível

Confira se o Ollama está rodando:

```powershell
ollama list
```

Confira o endpoint:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

Confira as variáveis:

```powershell
$env:OLLAMA_BASE_URL
$env:OLLAMA_MODEL
```

### Erro: tesseract não é reconhecido

Confirme instalação e `PATH`:

```powershell
tesseract --version
```

Adicione `C:\Program Files\Tesseract-OCR` ao `PATH`, feche e reabra o PowerShell.

### Erro de dependências Python

Atualize o `pip` e reinstale:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```
