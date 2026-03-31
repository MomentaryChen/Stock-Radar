#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_PATH="${SCRIPT_DIR}/infra"

if [[ ! -d "${INFRA_PATH}" ]]; then
  echo "infra directory not found: ${INFRA_PATH}" >&2
  exit 1
fi

cd "${INFRA_PATH}"
docker compose up -d --build
