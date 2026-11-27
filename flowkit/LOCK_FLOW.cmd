@echo off
cd /d "%~dp0"
start "" "%~dp0engines\muse\runtime\muse\python\pythonw.exe" -B "%~dp0app\flow_browser.py"
