@echo off
title AetherisClassifier - Setup Environment
color 0B

echo ============================================
echo   AetherisClassifier - Setup Environment
echo ============================================
echo.

set VENV_NAME=venv

:: 1. Verificar se Python esta instalado
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado! Instale o Python primeiro.
    pause
    exit /b 1
)
python --version
echo [OK] Python encontrado.
echo.

:: 2. Criar Virtual Environment
if exist "%VENV_NAME%" (
    echo [AVISO] A venv '%VENV_NAME%' ja existe. Deseja recriar? (s/N):
    set /p resposta=
    if /I "!resposta!"=="s" (
        echo [...] Removendo venv existente...
        rmdir /s /q "%VENV_NAME%"
        echo [OK] Venv antiga removida.
        py -3.12 -m venv %VENV_NAME%
        echo [OK] Virtual Environment criada em: %CD%\%VENV_NAME%
    ) else (
        echo [INFO] Utilizando venv existente.
    )
) else (
    echo [...] Criando Virtual Environment...
    py -3.12 -m venv %VENV_NAME%
    echo [OK] Virtual Environment criada em: %CD%\%VENV_NAME%
)
echo.

:: 3. Atualizar pip
echo [...] Atualizando pip...
call "%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo [OK] pip atualizado.
echo.

:: 4. Verificar requirements.txt
if not exist "requirements.txt" (
    echo [ERRO] Arquivo 'requirements.txt' nao encontrado em: %CD%
    pause
    exit /b 1
)
echo [OK] requirements.txt encontrado.
echo.

:: 5. Instalar dependencias
echo ============================================
echo   Instalando dependencias...
echo   Isso pode levar varios minutos.
echo ============================================
echo.

call "%VENV_NAME%\Scripts\python.exe" -m pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   INSTALACAO CONCLUIDA COM SUCESSO!
    echo ============================================
    echo.
    echo Para ativar a Virtual Environment:
    echo   %VENV_NAME%\Scripts\activate
    echo.
    echo Para iniciar o AetherisClassifier:
    echo   python ui_main.py
    echo.
    echo Ou usando o launcher:
    echo   python launcher.py
    echo.
) else (
    echo.
    echo [ERRO] Falha na instalacao de algumas dependencias.
    echo Tente instalar manualmente com:
    echo   %VENV_NAME%\Scripts\python.exe -m pip install -r requirements.txt
)

pause