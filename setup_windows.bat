@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
set "SETUP_EXIT=%ERRORLEVEL%"
echo.
if not "%SETUP_EXIT%"=="0" (
    echo Setup gagal. Baca pesan error di atas.
) else (
    echo Setup selesai. Anda dapat menutup jendela ini.
)
pause
exit /b %SETUP_EXIT%
