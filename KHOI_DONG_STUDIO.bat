@echo off
title Storyboard AI Studio Pro
cd /d "%~dp0"
if exist "Storyboard_AI_Studio.exe" (
    start "" "Storyboard_AI_Studio.exe"
    exit /b
)
if exist "studio\.venv\Scripts\pythonw.exe" (
    start "" "studio\.venv\Scripts\pythonw.exe" "studio\desktop_app.py"
) else (
    start "" python "studio\desktop_app.py"
)
