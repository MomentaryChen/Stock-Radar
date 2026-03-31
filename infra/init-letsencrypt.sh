#!/usr/bin/env sh
set -eu

DOMAIN_NAME="${DOMAIN_NAME:-stock-radar.ddns.net}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [ -z "${CERTBOT_EMAIL}" ]; then
  echo "CERTBOT_EMAIL is required. Please set it in your environment or .env file." >&2
  exit 1
fi

echo "[init-letsencrypt] Ensure nginx is up for ACME challenge..."
docker compose up -d nginx

echo "[init-letsencrypt] Requesting certificate for ${DOMAIN_NAME}..."
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAIN_NAME}" \
  --email "${CERTBOT_EMAIL}" \
  --agree-tos \
  --no-eff-email

echo "[init-letsencrypt] Reloading nginx..."
docker compose exec nginx nginx -s reload

echo "[init-letsencrypt] Done."
