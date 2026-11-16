param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$webRoot = Join-Path $projectRoot 'web'
$pythonPath = Join-Path $webRoot '.venv\Scripts\python.exe'
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Instala Node.js 22 o superior para preparar el SDK modular de Firebase.' }
Push-Location $webRoot
try {
    if (-not (Test-Path -LiteralPath (Join-Path $webRoot 'node_modules\firebase\package.json'))) {
        & npm ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias web.' }
    }
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo compilar el cliente Firebase.' }
} finally { Pop-Location }
if (-not (Test-Path -LiteralPath $pythonPath)) {
    & python -m venv (Join-Path $webRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el entorno Python.' }
}
& $pythonPath -m pip install -r (Join-Path $webRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias de Django.' }
Push-Location $webRoot
try {
    & $pythonPath manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'No se pudieron preparar las sesiones web.' }
    & $pythonPath manage.py runserver "127.0.0.1:$Port" --noreload
} finally {
    Pop-Location
}
