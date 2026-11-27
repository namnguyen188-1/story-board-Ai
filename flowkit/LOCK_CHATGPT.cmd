@echo off
title FlowKit - Lock ChatGPT Web
cd /d "%~dp0"
python -B "%~dp0app\chatgpt_browser.py" --lock
timeout /t 3
