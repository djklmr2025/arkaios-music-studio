@echo off
title ARKAIOS Spatial Music Studio (5 Planos 3D - Windows 11)
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================================================
echo   ARKAIOS SPATIAL MUSIC STUDIO - LANZADOR WINDOWS 11
echo ======================================================================
echo.

set PYTHON_EXE=C:\ARKAIOS\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo [ERROR] No se encontro el entorno Python en C:\ARKAIOS\.venv\Scripts\python.exe
    echo Por favor instala Python o verifica la ruta.
    pause
    exit /b 1
)

echo [*] Verificando batera de pruebas de ingeniera acstica...
"%PYTHON_EXE%" tests_run.py

echo.
echo [*] Iniciando interfaz interactiva de 5 planos (GUI)...
start "" "%PYTHON_EXE%" gui_studio.py

echo [OK] Estudio espacial iniciado con exito.
exit /b 0
