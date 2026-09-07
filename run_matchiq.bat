@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_matchiq.ps1"
set "RUN_EXIT=%ERRORLEVEL%"
echo.
if not "%RUN_EXIT%"=="0" (
    echo MatchIQ berhenti dengan error. Baca pesan di atas.
    pause
)
exit /b %RUN_EXIT%
