@echo off
:: ============================================================
::  Verra.bat - Launcher do Aetheris ToolBox
::  Executa main.py usando o interpretador da .venv do projeto.
::  Argumentos recebidos sao repassados para o main.py.
:: ============================================================
setlocal EnableExtensions

title Verra - AetherisToolBox

:: Diretorio de trabalho = raiz do projeto (config\, log\, resources\, plugins\)
cd /d "%~dp0"

:: Interpretador da virtual environment local do projeto.
:: Troque python.exe por pythonw.exe para iniciar sem janela de console.
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo ============================================
    echo   ERRO - Virtual environment nao encontrada
    echo ============================================
    echo.
    echo Esperado em: %VENV_PYTHON%
    echo.
    echo Crie o ambiente executando: setup_venv.bat
    echo.
    pause
    exit /b 1
)

"%VENV_PYTHON%" "%~dp0main.py" %*

set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERRO] A aplicacao finalizou com codigo %EXIT_CODE%.
    echo Verifique o log mais recente na pasta log\.
    echo.
    pause
)

endlocal & exit /b %EXIT_CODE%