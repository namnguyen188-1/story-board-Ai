@echo off
title FlowKit - Status Accounts
cd /d "%~dp0"
python -B "%~dp0app\status_accounts.py"
pause
