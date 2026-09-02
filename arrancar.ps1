Set-Location $PSScriptRoot
Write-Host "ENTRENARIA (fichas + chat) en http://127.0.0.1:8010"
if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    Write-Host "Creá el entorno: python -m venv .venv ; .\.venv\Scripts\pip.exe install -r requirements.txt"
    exit 1
}
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8010
