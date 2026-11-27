@echo off
title Storyboard AI Studio Pro
cd /d "%~dp0"

echo ======================================================================
echo    🎬 DANG KHOI DONG STORYBOARD AI STUDIO PRO (DESKTOP APP)...
echo ======================================================================

if exist "Storyboard_AI_Studio.exe" (
    start "" "Storyboard_AI_Studio.exe"
    exit /b 0
)

if exist "studio\runtime\python\python.exe" (
    start "" "studio\runtime\python\python.exe" "studio\desktop_app.py"
) else if exist "studio\.venv\Scripts\python.exe" (
    start "" "studio\.venv\Scripts\python.exe" "studio\desktop_app.py"
) else (
    start "" python "studio\desktop_app.py"
)
exit /b 0
