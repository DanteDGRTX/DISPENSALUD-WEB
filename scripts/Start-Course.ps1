param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
foreach ($tool in @('java','mvn','node')) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Falta $tool. Configura Java JDK 17+, Maven y Node 22+." }
}
foreach ($servicePort in @(8091,8092,$Port)) {
    if (Get-NetTCPConnection -LocalPort $servicePort -State Listen -ErrorAction SilentlyContinue) {
        throw "El puerto $servicePort ya está ocupado. No se modifica ese proceso."
    }
}
& mvn -B -f (Join-Path $projectRoot 'spring\pom.xml') verify
if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación o una prueba Spring. No se inicia la integración.' }
$previousToken = $env:DISPENSALUD_SUPERVISION_TOKEN
$previousUrl = $env:DISPENSALUD_SPRING_URL
$children = @()
try {
    $bytes = New-Object byte[] 48
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $env:DISPENSALUD_SUPERVISION_TOKEN = [Convert]::ToBase64String($bytes)
    $env:DISPENSALUD_SPRING_URL = 'http://127.0.0.1:8091'
    foreach ($service in @('supervision','portal')) {
        $jar = Join-Path $projectRoot "spring\$service\target\$service-1.0.0-SNAPSHOT.jar"
        $children += Start-Process java -ArgumentList @('-jar',('"' + $jar + '"')) -NoNewWindow -PassThru
    }
    foreach ($servicePort in @(8091,8092)) {
        $ready = $false
        for ($attempt=0; $attempt -lt 60; $attempt++) {
            if ($children | Where-Object { $_.HasExited }) { throw 'Un servicio Spring terminó. Revisa su mensaje de arranque.' }
            try {
                $result = Invoke-RestMethod "http://127.0.0.1:$servicePort/health" -TimeoutSec 1
                if ($result.status -eq 'ok') { $ready=$true; break }
            } catch {}
            Start-Sleep -Milliseconds 500
        }
        if (-not $ready) { throw "El servicio $servicePort no estuvo listo." }
    }
    & (Join-Path $PSScriptRoot 'Start-Web.ps1') -Port $Port
} finally {
    foreach ($child in $children) { if (-not $child.HasExited) { Stop-Process -Id $child.Id -ErrorAction SilentlyContinue } }
    $env:DISPENSALUD_SUPERVISION_TOKEN = $previousToken
    $env:DISPENSALUD_SPRING_URL = $previousUrl
}
