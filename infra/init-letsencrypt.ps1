Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$domainName = if ($env:DOMAIN_NAME) { $env:DOMAIN_NAME } else { "stock-radar.ddns.net" }
$certbotEmail = $env:CERTBOT_EMAIL

if ([string]::IsNullOrWhiteSpace($certbotEmail)) {
  throw "CERTBOT_EMAIL is required. Please set it in your environment or .env file."
}

Write-Host "[init-letsencrypt] Ensure nginx is up for ACME challenge..."
docker compose --profile prod up -d nginx

Write-Host "[init-letsencrypt] Requesting certificate for $domainName..."
docker compose --profile prod run --rm certbot certonly `
  --webroot -w /var/www/certbot `
  -d $domainName `
  --email $certbotEmail `
  --agree-tos `
  --no-eff-email

Write-Host "[init-letsencrypt] Reloading nginx..."
docker compose --profile prod exec nginx nginx -s reload

Write-Host "[init-letsencrypt] Done."
