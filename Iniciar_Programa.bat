@echo off
chcp 65001 > nul
title Vanilla DC Bot Manager
cd /d "%~dp0"

if exist "DiscordSimpleBotClient.exe" (
    start "" "DiscordSimpleBotClient.exe"
) else if exist "dist\DiscordSimpleBotClient\DiscordSimpleBotClient.exe" (
    start "" "dist\DiscordSimpleBotClient\DiscordSimpleBotClient.exe"
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" voice_stream_app.py
) else (
    python voice_stream_app.py
)
