Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infraPath = Join-Path $PSScriptRoot "infra"
if (-not (Test-Path $infraPath)) {
  throw "infra directory not found: $infraPath"
}

Push-Location $infraPath
try {
  docker compose up -d --build
  Write-Host "[buildAndStart] Done."
  Write-Host "[buildAndStart] If this is your first HTTPS deployment, run:"
  Write-Host "  cd infra"
  Write-Host "  `$env:DOMAIN_NAME=`"stock-radar.ddns.net`""
  Write-Host "  `$env:CERTBOT_EMAIL=`"you@example.com`""
  Write-Host "  ./init-letsencrypt.ps1"
}
finally {
  Pop-Location
}
