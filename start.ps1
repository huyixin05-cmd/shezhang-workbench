param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$env:PYTHONUTF8 = '1'
$env:TEACH_DATA_DIR = Join-Path $PSScriptRoot '.data'
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $pythonPath)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv .venv
    } else {
        throw 'Install Python 3.11 or newer from python.org, then run this launcher again.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create Python environment.' }
}
& $pythonPath -c "import sys; assert sys.version_info >= (3,11), 'Python 3.11+ required'"
if ($LASTEXITCODE -ne 0) { throw 'Python 3.11+ required. Recreate .venv with a supported Python.' }
$stamp = Join-Path $PSScriptRoot '.venv\teach-installed.sha256'
$digest = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'requirements.lock') -Algorithm SHA256).Hash
if (!(Test-Path -LiteralPath $stamp) -or (Get-Content -LiteralPath $stamp -Raw).Trim() -ne $digest) {
    & $pythonPath -m pip install -r requirements.lock
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your network and retry.' }
    Set-Content -LiteralPath $stamp -Value $digest -Encoding ASCII
}
if (!(Test-Path -LiteralPath 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe') -and !(Test-Path -LiteralPath 'C:\Program Files\Google\Chrome\Application\chrome.exe')) {
    & $pythonPath -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Browser installation failed. Retry after checking your network.' }
}
& $pythonPath -m teach_agent --data-dir $env:TEACH_DATA_DIR --port $Port --open
if ($LASTEXITCODE -ne 0) { throw 'The workbench did not start. Check whether it is already running.' }
