@echo off
chcp 65001 >nul
title Movie Recap Studio Pro
cd /d "%~dp0"

if exist "Movie_Recap_Studio.exe" (
    start "" "Movie_Recap_Studio.exe"
    exit /b
)

if exist "runtime\python\pythonw.exe" (
    start "" "runtime\python\pythonw.exe" qt6_app.py
    exit /b
)

if exist "runtime\python\python.exe" (
    "runtime\python\python.exe" qt6_app.py
    pause
    exit /b
)

echo [LỖI] Không tìm thấy runtime Python hoặc Movie_Recap_Studio.exe!
echo Vui lòng đảm bảo bạn đã giải nén đầy đủ thư mục của phần mềm.
pause
