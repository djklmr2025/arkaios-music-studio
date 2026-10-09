@echo off
setlocal
title ARKAIOS Spatial Music Studio
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto error
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
".venv\Scripts\python.exe" tests_run.py
if errorlevel 1 goto error
".venv\Scripts\python.exe" gui_studio.py
if errorlevel 1 goto error
exit /b 0
:error
echo [ERROR] No se pudo iniciar. Instala Python 3 con el lanzador py y revisa el mensaje anterior.
pause
exit /b 1
