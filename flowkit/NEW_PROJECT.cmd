@echo off
cd /d "%~dp0"
"%~dp0engines\muse\runtime\muse\python\python.exe" -B -u "%~dp0app\clone_project.py" %*
pause
