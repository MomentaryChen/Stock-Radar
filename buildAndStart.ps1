Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infraPath = Join-Path $PSScriptRoot "infra"
if (-not (Test-Path $infraPath)) {
  throw "infra directory not found: $infraPath"
}

Push-Location $infraPath
try {
  docker compose up -d --build
}
finally {
  Pop-Location
}
