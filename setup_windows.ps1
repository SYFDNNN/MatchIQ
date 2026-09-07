[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvRoot = Join-Path $env:LOCALAPPDATA "piala-dunia-26-hybrid-ai-v4-venv"
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$Requirements = Join-Path $ProjectRoot "requirements.txt"
$EnsureModelScript = Join-Path $ProjectRoot "scripts\ensure_runtime_model.py"
$VerifyScript = Join-Path $ProjectRoot "scripts\verify_setup.py"
$KernelName = "piala-dunia-26-hybrid-ai-v4"
$KernelDisplayName = "Python 3.12 (MatchIQ Hybrid AI)"

Write-Host "[1/6] Memeriksa Python 3.12 64-bit..."
$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($null -eq $PyLauncher) {
    throw "Python Launcher (py.exe) tidak ditemukan. Instal Python 3.12 64-bit dari python.org, lalu jalankan setup ini lagi."
}

& $PyLauncher.Source -3.12 -c "import platform, sys; assert sys.version_info[:2] == (3, 12); assert platform.architecture()[0] == '64bit'; print(sys.version)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.12 64-bit tidak tersedia. Coba jalankan: py -3.12 --version"
}

Write-Host "[2/6] Menyiapkan virtual environment di luar folder proyek..."
if ((Test-Path $VenvRoot) -and -not (Test-Path $VenvPython)) {
    throw "Folder environment ada tetapi tidak lengkap: $VenvRoot. Ubah nama atau hapus folder tersebut, lalu jalankan setup lagi."
}
if (-not (Test-Path $VenvPython)) {
    & $PyLauncher.Source -3.12 -m venv $VenvRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Gagal membuat virtual environment di $VenvRoot"
    }
}

Write-Host "[3/6] Memasang dependency dari requirements.txt..."
& $VenvPython -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "Gagal memperbarui pip/setuptools/wheel." }
& $VenvPython -m pip install --requirement $Requirements
if ($LASTEXITCODE -ne 0) { throw "Gagal memasang dependency proyek." }

Write-Host "[4/6] Mendaftarkan kernel Jupyter untuk VS Code..."
& $VenvPython -m ipykernel install --user --name $KernelName --display-name $KernelDisplayName
if ($LASTEXITCODE -ne 0) { throw "Gagal mendaftarkan kernel Jupyter." }

Write-Host "[5/6] Menyiapkan runtime native Piala Dunia dan UCL untuk Windows..."
& $VenvPython $EnsureModelScript
if ($LASTEXITCODE -ne 0) { throw "Gagal menyiapkan runtime Piala Dunia/UCL." }

Write-Host "[6/6] Memverifikasi environment, data, model, dan Flask..."
& $VenvPython $VerifyScript
if ($LASTEXITCODE -ne 0) { throw "Verifikasi setup gagal." }

Write-Host ""
Write-Host "SETUP BERHASIL" -ForegroundColor Green
Write-Host "Interpreter : $VenvPython"
Write-Host "Kernel      : $KernelDisplayName"
Write-Host "Model       : Piala Dunia + UEFA Champions League"
Write-Host "Web UI      : jalankan run_matchiq.bat"
Write-Host "Notebook    : Piala Dunia + UCL; pilih kernel di atas untuk Run All."
