<#
.SYNOPSIS
  Instala e configura o AIQuestionResponse no Windows com Ollama local obrigatório.

.DESCRIPTION
  O script prioriza instalar dados pesados fora do disco do sistema:
  - cria ambiente virtual Python em $InstallRoot\.venv;
  - define cache do pip em $InstallRoot\pip-cache;
  - define modelos do Ollama em $InstallRoot\ollama-models;
  - tenta instalar Python, Ollama e Tesseract via winget com --location em $InstallRoot\Apps.

  Quando um instalador winget não suporta --location, o script tenta novamente sem --location,
  mas mantém venv, cache pip e modelos Ollama fora do disco do sistema.
#>

[CmdletBinding()]
param(
    [string]$InstallRoot = "",
    [string]$Model = "qwen2.5:14b-instruct-q4_K_M",
    [switch]$SkipWingetInstall,
    [switch]$SkipModelPull,
    [switch]$RunTests
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Info {
    param([string]$Message)
    Write-Host "    $Message" -ForegroundColor Gray
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-RepoRoot {
    $scriptPath = $PSCommandPath
    if (-not $scriptPath) {
        return (Get-Location).Path
    }
    return (Resolve-Path (Join-Path (Split-Path -Parent $scriptPath) "..")).Path
}

function Get-DefaultInstallRoot {
    $systemDrive = $env:SystemDrive.TrimEnd("\")
    $candidate = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
        Where-Object { $_.DeviceID -ne $systemDrive } |
        Sort-Object FreeSpace -Descending |
        Select-Object -First 1

    if ($candidate) {
        return (Join-Path $candidate.DeviceID "AIQuestionResponse")
    }

    return (Join-Path $env:USERPROFILE "AIQuestionResponse")
}

function Set-UserAndProcessEnv {
    param(
        [string]$Name,
        [string]$Value
    )
    [Environment]::SetEnvironmentVariable($Name, $Value, "User")
    Set-Item -Path "Env:$Name" -Value $Value
}


function Update-PathFromRegistry {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = @($machinePath, $userPath) -join ";"
}

function Add-UserPathEntry {
    param([string]$PathEntry)

    if (-not (Test-Path $PathEntry)) {
        return
    }

    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $entries = @()
    if ($userPath) {
        $entries = $userPath -split ";" | Where-Object { $_ }
    }

    if ($entries -notcontains $PathEntry) {
        $newPath = (@($entries) + $PathEntry) -join ";"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    if (($env:Path -split ";") -notcontains $PathEntry) {
        $env:Path = "$PathEntry;$env:Path"
    }
}

function Invoke-WingetInstall {
    param(
        [string]$Id,
        [string]$Name,
        [string]$Location = ""
    )

    if ($SkipWingetInstall) {
        Write-Info "Pulando winget para $Name por causa de -SkipWingetInstall."
        return
    }

    if (-not (Test-Command "winget")) {
        throw "winget não encontrado. Instale o App Installer pela Microsoft Store ou use -SkipWingetInstall após instalar os pré-requisitos manualmente."
    }

    $baseArgs = @(
        "install",
        "--id", $Id,
        "-e",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--silent"
    )

    if ($Location) {
        Write-Info "Tentando instalar $Name em $Location."
        & winget @baseArgs --location $Location
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Write-Warning "Instalação de $Name com --location falhou. Tentando sem --location. Código: $LASTEXITCODE"
    }

    Write-Info "Instalando $Name com local padrão do instalador."
    & winget @baseArgs
    if ($LASTEXITCODE -ne 0) {
        throw "winget falhou ao instalar $Name. Código: $LASTEXITCODE"
    }
}

function Get-PythonCommand {
    if (Test-Command "py") {
        return "py"
    }
    if (Test-Command "python") {
        return "python"
    }
    throw "Python não encontrado no PATH após a instalação. Feche e reabra o PowerShell ou instale Python 3.11+."
}

function Wait-Ollama {
    param([int]$TimeoutSeconds = 45)

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        try {
            Invoke-RestMethod -Uri "$env:OLLAMA_BASE_URL/api/tags" -Method Get -TimeoutSec 3 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }
    return $false
}

$repoRoot = Get-RepoRoot
if (-not $InstallRoot) {
    $InstallRoot = Get-DefaultInstallRoot
}
$InstallRoot = [System.IO.Path]::GetFullPath($InstallRoot)

$appsRoot = Join-Path $InstallRoot "Apps"
$venvPath = Join-Path $InstallRoot ".venv"
$pipCache = Join-Path $InstallRoot "pip-cache"
$ollamaModels = Join-Path $InstallRoot "ollama-models"
$tesseractInstall = Join-Path $appsRoot "Tesseract-OCR"
$ollamaInstall = Join-Path $appsRoot "Ollama"
$pythonInstall = Join-Path $appsRoot "Python311"

Write-Step "Resumo da instalação"
Write-Info "Repositório: $repoRoot"
Write-Info "Raiz de instalação: $InstallRoot"
Write-Info "Ambiente virtual: $venvPath"
Write-Info "Cache pip: $pipCache"
Write-Info "Modelos Ollama: $ollamaModels"
Write-Info "Modelo Ollama: $Model"

Write-Step "Criando diretórios fora do disco do sistema quando possível"
New-Item -ItemType Directory -Force -Path $InstallRoot, $appsRoot, $pipCache, $ollamaModels | Out-Null

Write-Step "Instalando pré-requisitos via winget quando necessário"
if (-not (Test-Command "py") -and -not (Test-Command "python")) {
    Invoke-WingetInstall -Id "Python.Python.3.11" -Name "Python 3.11" -Location $pythonInstall
}
else {
    Write-Info "Python já encontrado."
}

if (-not (Test-Command "ollama")) {
    Invoke-WingetInstall -Id "Ollama.Ollama" -Name "Ollama" -Location $ollamaInstall
}
else {
    Write-Info "Ollama já encontrado."
}

if (-not (Test-Command "tesseract")) {
    Invoke-WingetInstall -Id "UB-Mannheim.TesseractOCR" -Name "Tesseract OCR" -Location $tesseractInstall
}
else {
    Write-Info "Tesseract já encontrado."
}

Update-PathFromRegistry
Add-UserPathEntry -PathEntry $tesseractInstall
Add-UserPathEntry -PathEntry (Join-Path $ollamaInstall "app")
Add-UserPathEntry -PathEntry $ollamaInstall

Write-Step "Configurando variáveis de ambiente persistentes"
Set-UserAndProcessEnv -Name "PIP_CACHE_DIR" -Value $pipCache
Set-UserAndProcessEnv -Name "OLLAMA_BASE_URL" -Value "http://localhost:11434"
Set-UserAndProcessEnv -Name "OLLAMA_MODELS" -Value $ollamaModels
Set-UserAndProcessEnv -Name "OLLAMA_MODEL" -Value $Model
Write-Info "Variáveis configuradas no usuário atual e nesta sessão."

Write-Step "Criando ambiente virtual fora do disco do sistema"
$pythonCommand = Get-PythonCommand
if (-not (Test-Path $venvPath)) {
    if ($pythonCommand -eq "py") {
        & py -3.11 -m venv $venvPath
    }
    else {
        & python -m venv $venvPath
    }
}
else {
    Write-Info "Ambiente virtual já existe."
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Python do ambiente virtual não encontrado em $venvPython."
}

Write-Step "Instalando dependências Python no ambiente virtual"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e "$repoRoot[dev]"

Write-Step "Validando ou iniciando Ollama"
if (-not (Test-Command "ollama")) {
    throw "O comando ollama ainda não está disponível. Feche e reabra o PowerShell ou confira a instalação."
}

if (-not (Wait-Ollama -TimeoutSeconds 8)) {
    Write-Info "Servidor Ollama não respondeu; tentando iniciar 'ollama serve' em segundo plano."
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized | Out-Null
}

if (-not (Wait-Ollama -TimeoutSeconds 45)) {
    throw "Ollama não respondeu em $env:OLLAMA_BASE_URL. Inicie manualmente com: ollama serve"
}

if (-not $SkipModelPull) {
    Write-Step "Baixando/validando modelo obrigatório do Ollama"
    & ollama pull $Model
}
else {
    Write-Info "Pulando download do modelo por causa de -SkipModelPull."
}

Write-Step "Criando atalho de inicialização no InstallRoot"
$startScript = Join-Path $InstallRoot "Start-AIQuestionResponse.ps1"
$startScriptContent = @"
`$env:OLLAMA_BASE_URL = "http://localhost:11434"
`$env:OLLAMA_MODEL = "$Model"
`$env:OLLAMA_MODELS = "$ollamaModels"
`$env:PIP_CACHE_DIR = "$pipCache"
& "$venvPython" -m ai_question_response
"@
Set-Content -Path $startScript -Value $startScriptContent -Encoding UTF8

Write-Step "Validando instalação da aplicação"
& $venvPython -c "from ai_question_response.core.agent import QuestionAgent; print('AIQuestionResponse import OK')"
Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 10 | Out-Null

if ($RunTests) {
    Write-Step "Executando testes e lint"
    & $venvPython -m pytest $repoRoot
    & $venvPython -m ruff check $repoRoot
}

Write-Step "Instalação concluída"
Write-Host "Para iniciar a aplicação:" -ForegroundColor Green
Write-Host "  & '$startScript'" -ForegroundColor Green
Write-Host "Ou diretamente:" -ForegroundColor Green
Write-Host "  & '$venvPython' -m ai_question_response" -ForegroundColor Green
Write-Host "Depois abra: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Para testar o Ollama da API local após iniciar a aplicação:" -ForegroundColor Green
Write-Host "  Invoke-RestMethod http://127.0.0.1:8000/health/ollama" -ForegroundColor Green
