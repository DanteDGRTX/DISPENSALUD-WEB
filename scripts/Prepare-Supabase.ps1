$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $projectRoot 'web/.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Falta el entorno Python del proyecto. No se inicia la preparación.' }
& $python (Join-Path $PSScriptRoot 'prepare_supabase.py')
if ($LASTEXITCODE -ne 0) { throw 'La preparación no terminó correctamente. Revisa el mensaje anterior, sin compartir contraseñas.' }
