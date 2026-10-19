param([int]$Port = 8080)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtimeDirectory = Join-Path $projectRoot 'data'
$accessPath = Join-Path $runtimeDirectory 'acceso-local.json'
New-Item -ItemType Directory -Force $runtimeDirectory | Out-Null
if (-not (Test-Path -LiteralPath $accessPath)) {
    $randomBytes = New-Object byte[] 24
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $generator.GetBytes($randomBytes)
    $generator.Dispose()
    $access = @{
        caregiver = 'cuidador.demo'
        olderAdult = 'usuario.demo'
        password = [Convert]::ToBase64String($randomBytes)
        note = 'Solo cuentas ficticias locales. Este archivo esta excluido de Git.'
    }
    $access | ConvertTo-Json | Set-Content -LiteralPath $accessPath -Encoding UTF8
}
$access = Get-Content -LiteralPath $accessPath -Raw | ConvertFrom-Json
$previousPassword = $env:DISPENSALUD_DEMO_PASSWORD
$previousPort = $env:API_PORT
$previousProfile = $env:SPRING_PROFILES_ACTIVE
$env:DISPENSALUD_DEMO_PASSWORD = $access.password
$env:API_PORT = [string]$Port
$env:SPRING_PROFILES_ACTIVE = 'local'
Push-Location (Join-Path $projectRoot 'api')
try {
    Write-Host "API local en http://127.0.0.1:$Port. Accesos de prueba en $accessPath"
    & mvn -q spring-boot:run
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo iniciar la API. Revisa Java, Maven y el puerto.' }
} finally {
    Pop-Location
    $env:DISPENSALUD_DEMO_PASSWORD = $previousPassword
    $env:API_PORT = $previousPort
    $env:SPRING_PROFILES_ACTIVE = $previousProfile
}
