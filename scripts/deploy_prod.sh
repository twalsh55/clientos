#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

echo "Deploying API first"
"${ROOT_DIR}/scripts/deploy_api.sh"

echo
echo "Deploying frontend second"
"${ROOT_DIR}/scripts/deploy_web.sh"
