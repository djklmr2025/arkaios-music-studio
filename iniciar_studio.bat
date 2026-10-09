@echo off
setlocal enabledelayedexpansion
title ARKAIOS Spatial Music Studio
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Buscando interprete de Python 3 para inicializar el entorno .venv...
    set "PY_EXEC="

    where py >nul 2>nul
    if !errorlevel! equ 0 (
        py -3 --version >nul 2>nul
        if !errorlevel! equ 0 set "PY_EXEC=py -3"
    )

    if not defined PY_EXEC (
        where python >nul 2>nul
        if !errorlevel! equ 0 (
            python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
            if !errorlevel! equ 0 set "PY_EXEC=python"
        )
    )

    if not defined PY_EXEC (
        for %%P in (
            "C:\Python314\python.exe"
            "C:\Python313\python.exe"
            "C:\Python312\python.exe"
            "C:\Python311\python.exe"
            "C:\Python310\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
            "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
            "%ProgramFiles%\Python314\python.exe"
            "%ProgramFiles%\Python313\python.exe"
            "%ProgramFiles%\Python312\python.exe"
            "%ProgramFiles%\Python311\python.exe"
        ) do (
            if not defined PY_EXEC (
                if exist %%P set "PY_EXEC=%%~P"
            )
        )
    )

    if not defined PY_EXEC (
        echo [ERROR] No se encontro un interprete valido de Python 3.10+ en el sistema.
        echo Instala Python desde https://www.python.org y asegurate de marcar 'Add python.exe to PATH'.
        goto error
    )

    echo [INFO] Creando entorno virtual .venv con: !PY_EXEC!
    !PY_EXEC! -m venv .venv
    if errorlevel 1 goto error
)

echo [1/3] Verificando dependencias en .venv...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error

echo [2/3] Ejecutando bateria de pruebas acusticas...
".venv\Scripts\python.exe" tests_run.py
if errorlevel 1 goto error

echo [3/3] Iniciando interfaz grafica de Windows 11...
start "" ".venv\Scripts\python.exe" gui_studio.py
exit /b 0

:error
echo.
echo [ERROR] No se pudo iniciar ARKAIOS Spatial Music Studio. Revisa los mensajes anteriores.
pause
exit /b 1
