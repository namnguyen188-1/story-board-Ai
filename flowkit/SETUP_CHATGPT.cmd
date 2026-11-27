@echo off
title FlowKit - Setup ChatGPT Web
cd /d "%~dp0"
echo ========================================================
echo   FLOWKIT - KHOI DONG TRINH DUYET CHATGPT WEB RIENG BIET
echo   (Profile rieng, cong CDP 9468, tach biet 100%% voi Flow)
echo ========================================================
python -B "%~dp0app\chatgpt_browser.py"
echo.
echo Hay dang nhap tai khoan ChatGPT Web cua ban tren cua so Chrome vua hien.
echo Khi dang nhap xong, ban co the chay LOCK_CHATGPT.cmd de an cua so.
echo ========================================================
pause
