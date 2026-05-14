#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEB_BASE_URL="${WEB_BASE_URL:-https://www.brivoly.com}"
VERCEL_CMD=(npx vercel)

cd "${ROOT_DIR}"

if ! command -v npx >/dev/null 2>&1; then
  echo "Missing required command: npx" >&2
  exit 1
fi

echo "Checking Vercel authentication"
"${VERCEL_CMD[@]}" whoami

echo "Deploying Next.js frontend from web/"
"${VERCEL_CMD[@]}" deploy --prod --yes --cwd web

echo "Checking ${WEB_BASE_URL}"
curl --fail --silent --show-error --head "${WEB_BASE_URL}"
echo

echo "Checking ${WEB_BASE_URL}/api/session"
curl --fail --silent --show-error "${WEB_BASE_URL}/api/session"
echo
