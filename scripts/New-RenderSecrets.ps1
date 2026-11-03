$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$directory = Join-Path $projectRoot 'data'
$destination = Join-Path $directory 'render.env'
if (Test-Path -LiteralPath $destination) { throw 'Ya existe data/render.env. No se sobrescriben los secretos existentes.' }
New-Item -ItemType Directory -Force $directory | Out-Null
function New-RandomValue([int]$Length) {
    $bytes = New-Object byte[] $Length
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
$values = @(
    'DJANGO_DEBUG=0'
    'DISPENSALUD_HOSTED_DEMO=1'
    ('DJANGO_SECRET_KEY=' + (New-RandomValue 32))
    ('DISPENSALUD_DEMO_PASSWORD=' + (New-RandomValue 24))
)
$values | Set-Content -LiteralPath $destination -Encoding utf8
Write-Host 'Secretos generados en data/render.env, fuera de Git y del contexto Docker. No los compartas por chat.'
