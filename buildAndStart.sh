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
if [ ! -f "${DOCKER_CONFIG}/config.json" ]; then
  printf '{"auths":{}}\n' > "${DOCKER_CONFIG}/config.json"
fi
docker compose up -d --build
