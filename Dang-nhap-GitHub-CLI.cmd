@echo off
setlocal
title Dang nhap GitHub CLI cho Storyboard AI
echo Dang nhap GitHub CLI bang tai khoan namnguyen188-1.
echo Ma xac nhan chi hien tren PC nay. Khong gui ma vao chat.
echo GitHub se yeu cau ban tu chap thuan quyen cho GitHub CLI.
echo.
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; $f=Join-Path $env:LOCALAPPDATA 'StoryboardAI\DeveloperTools\GitHubCLI\gh-path.txt'; if(-not (Test-Path $f)){throw 'GitHub CLI chua san sang'}; $g=(Get-Content -LiteralPath $f -Raw).Trim(); & $g auth login --hostname github.com --git-protocol https --web; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}; & $g api user --jq .login"
echo.
if errorlevel 1 (
  echo Dang nhap chua hoan tat.
) else (
  echo Da hoan tat. Bao lai de tiep tuc phat hanh Storyboard AI.
)
pause
