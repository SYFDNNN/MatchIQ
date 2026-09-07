[CmdletBinding()]
param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvRoot = Join-Path $env:LOCALAPPDATA "piala-dunia-26-hybrid-ai-v4-venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$AppPath = Join-Path $ProjectRoot "app.py"
$EnsureModelScript = Join-Path $ProjectRoot "scripts\ensure_runtime_model.py"

if (-not (Test-Path $VenvPython)) {
    throw "Environment MatchIQ belum tersedia. Jalankan setup_windows.bat terlebih dahulu."
}
if (-not (Test-Path $AppPath)) {
    throw "app.py tidak ditemukan di $ProjectRoot"
}

Write-Host "Memeriksa runtime Piala Dunia dan UCL..."
& $VenvPython $EnsureModelScript
if ($LASTEXITCODE -ne 0) {
    throw "Runtime Piala Dunia/UCL tidak dapat disiapkan. Jalankan setup_windows.bat kembali."
}

Write-Host "Menjalankan MatchIQ di http://127.0.0.1:$Port" -ForegroundColor Cyan
Write-Host "Tekan Ctrl+C untuk menghentikan server."
& $VenvPython $AppPath --host 127.0.0.1 --port $Port --open-browser
exit $LASTEXITCODE
