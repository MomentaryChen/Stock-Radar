Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$infraPath = Join-Path $PSScriptRoot "infra"
if (-not (Test-Path $infraPath)) {
  throw "infra directory not found: $infraPath"
}

Push-Location $infraPath
try {
  $deployEnv = if ($env:DEPLOY_ENV) { $env:DEPLOY_ENV } else { "local" }

  if ($deployEnv -eq "prod") {
    docker compose --profile prod up -d --build
  }
  else {
    docker compose up -d --build
  }

  Write-Host "[buildAndStart] Done."
  Write-Host "[buildAndStart] DEPLOY_ENV=$deployEnv (default: local)."
  if ($deployEnv -eq "prod") {
    Write-Host "[buildAndStart] If this is your first HTTPS deployment, run:"
    Write-Host "  cd infra"
    Write-Host "  `$env:DOMAIN_NAME=`"stock-radar.ddns.net`""
    Write-Host "  `$env:CERTBOT_EMAIL=`"you@example.com`""
    Write-Host "  ./init-letsencrypt.ps1"
  }
}
finally {
  Pop-Location
}
