@echo off
title Discord Simple Bot Client
echo ========================================================
echo         INICIANDO DISCORD SIMPLE BOT CLIENT...
echo ========================================================
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" "voice_stream_app.py"
) else (
    python "voice_stream_app.py"
)
