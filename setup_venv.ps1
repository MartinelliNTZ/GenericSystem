<#
.SYNOPSIS
    AetherisClassifier - Configuracao do Ambiente Virtual

.DESCRIPTION
    Cria uma virtual environment (.venv) usando Python 3.12,
    atualiza o pip e instala todas as dependencias do
    requirements.txt.
#>

$ErrorActionPreference = "Stop"
$VENV_DIR = ".venv"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " AetherisClassifier - Setup do Ambiente" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --------------------------------------------------
# Verifica se Python 3.12 existe
# --------------------------------------------------
try {
    $pyVer = py -3.12 --version 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw
    }

    Write-Host "[INFO] $pyVer detectado." -ForegroundColor Green
}
catch {
    Write-Host "[ERRO] Python 3.12 nao encontrado!" -ForegroundColor Red
    Write-Host "Instale o Python 3.12 e tente novamente." -ForegroundColor Red
    exit 1
}

Write-Host ""

# --------------------------------------------------
# Passo 1 - Criar a virtual environment
# --------------------------------------------------
if (Test-Path "$VENV_DIR\Scripts\python.exe") {

    Write-Host "[OK] Virtual environment ja existe em .venv" -ForegroundColor Green

    $venvVersion = & "$VENV_DIR\Scripts\python.exe" --version
    Write-Host "[INFO] Venv usando: $venvVersion" -ForegroundColor Cyan
}
else {

    Write-Host "[1/3] Criando virtual environment com Python 3.12..." -ForegroundColor Yellow

    py -3.12 -m venv $VENV_DIR

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERRO] Falha ao criar virtual environment." -ForegroundColor Red
        exit 1
    }

    Write-Host "[OK] Virtual environment criada em .venv" -ForegroundColor Green
}

Write-Host ""

# --------------------------------------------------
# Passo 2 - Atualizar pip
# --------------------------------------------------
Write-Host "[2/3] Atualizando pip..." -ForegroundColor Yellow

& "$VENV_DIR\Scripts\python.exe" -m pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERRO] Falha ao atualizar pip." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Pip atualizado." -ForegroundColor Green
Write-Host ""

# --------------------------------------------------
# Passo 3 - Instalar dependencias
# --------------------------------------------------
if (-not (Test-Path "requirements.txt")) {
    Write-Host "[ERRO] requirements.txt nao encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "[3/3] Instalando dependencias do requirements.txt..." -ForegroundColor Yellow
Write-Host ""

& "$VENV_DIR\Scripts\python.exe" -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[AVISO] Algumas dependencias podem ter falhado." -ForegroundColor Yellow
    Write-Host "Verifique os erros exibidos acima." -ForegroundColor Yellow
}
else {
    Write-Host ""
    Write-Host "[OK] Todas as dependencias instaladas com sucesso." -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Instalacao concluida!" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host " Para ativar o ambiente:" -ForegroundColor White
Write-Host "     .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""

Write-Host " Para iniciar o projeto:" -ForegroundColor White
Write-Host "     python launcher.py" -ForegroundColor Yellow
Write-Host ""