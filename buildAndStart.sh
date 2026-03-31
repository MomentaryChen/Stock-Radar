#!/usr/bin/env sh
set -eu

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INFRA_PATH="${SCRIPT_DIR}/infra"

if [ ! -d "${INFRA_PATH}" ]; then
  echo "infra directory not found: ${INFRA_PATH}" >&2
  exit 1
fi

cd "${INFRA_PATH}"
# Use a local Docker config fallback on headless Linux hosts
# to avoid credential helper failures (e.g. secretservice DBus).
export DOCKER_CONFIG="${DOCKER_CONFIG:-/tmp/docker-nokeyring}"
mkdir -p "${DOCKER_CONFIG}"
# Always write a helper-free config to prevent credential helper lookup.
printf '{"auths":{}}\n' > "${DOCKER_CONFIG}/config.json"
# Avoid BuildKit metadata credential lookups on older headless hosts.
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
DEPLOY_ENV="${DEPLOY_ENV:-local}"

echo "[buildAndStart] Pulling base images..."
docker --config "${DOCKER_CONFIG}" pull postgres:16-alpine
docker --config "${DOCKER_CONFIG}" pull python:3.11-slim
docker --config "${DOCKER_CONFIG}" pull node:20-alpine
if [ "${DEPLOY_ENV}" = "prod" ]; then
  docker --config "${DOCKER_CONFIG}" pull nginx:1.27-alpine
  docker --config "${DOCKER_CONFIG}" pull certbot/certbot:latest
fi

echo "[buildAndStart] Stopping running services before build..."
if [ "${DEPLOY_ENV}" = "prod" ]; then
  docker --config "${DOCKER_CONFIG}" compose --profile prod down --remove-orphans
else
  docker --config "${DOCKER_CONFIG}" compose down --remove-orphans
fi

echo "[buildAndStart] Building and starting services with compose..."
if [ "${DEPLOY_ENV}" = "prod" ]; then
  docker --config "${DOCKER_CONFIG}" compose --profile prod up -d --build --remove-orphans
else
  docker --config "${DOCKER_CONFIG}" compose up -d --build --remove-orphans
fi

echo "[buildAndStart] Done."
