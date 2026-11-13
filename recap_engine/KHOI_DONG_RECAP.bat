@echo off
chcp 65001 >nul
title Khởi Động Movie Recap Studio Pro
cd /d "%~dp0"

if exist "Movie_Recap_Studio.exe" (
    start "" "Movie_Recap_Studio.exe"
    exit /b
)

if exist "..\studio\runtime\python\python.exe" (
    start "" "..\studio\runtime\python\python.exe" -u "qt6_app.py"
) else (
    start "" python -u "qt6_app.py"
)
exit /b
