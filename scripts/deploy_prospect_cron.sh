#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAILWAY_CMD=(npx @railway/cli@latest)
FUNCTION_NAME="${FUNCTION_NAME:-prospect-hourly}"
FUNCTION_PATH="${FUNCTION_PATH:-railway-functions/prospect-hourly.ts}"
FUNCTION_CRON="${FUNCTION_CRON:-0 * * * *}"
API_BASE_URL="${API_BASE_URL:-https://api.brivoly.com}"

cd "${ROOT_DIR}"

log() {
  printf '\n[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

if ! command -v npx >/dev/null 2>&1; then
  echo "Missing required command: npx" >&2
  exit 1
fi

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  . ".env"
  set +a
fi

for required_var in TELEGRAM_WEBHOOK_SECRET TELEGRAM_CHAT_ID; do
  if [ -z "${!required_var:-}" ]; then
    echo "Missing required variable: ${required_var}" >&2
    exit 1
  fi
done

if [ ! -f "${FUNCTION_PATH}" ]; then
  echo "Function file not found: ${FUNCTION_PATH}" >&2
  exit 1
fi

log "Checking Railway authentication and project linkage"
"${RAILWAY_CMD[@]}" whoami
"${RAILWAY_CMD[@]}" status

log "Ensuring Railway function ${FUNCTION_NAME} exists"
if "${RAILWAY_CMD[@]}" functions list | rg -qx "${FUNCTION_NAME}"; then
  log "Function already exists; pushing latest code"
  "${RAILWAY_CMD[@]}" functions push -p "${FUNCTION_PATH}"
else
  log "Creating function with hourly cron"
  "${RAILWAY_CMD[@]}" functions new \
    -n "${FUNCTION_NAME}" \
    -p "${FUNCTION_PATH}" \
    -c "${FUNCTION_CRON}" \
    --http false \
    --serverless true
fi

log "Configuring function environment"
"${RAILWAY_CMD[@]}" variable set "API_BASE_URL=${API_BASE_URL}" --service "${FUNCTION_NAME}" --skip-deploys >/dev/null
printf '%s' "${TELEGRAM_WEBHOOK_SECRET}" | "${RAILWAY_CMD[@]}" variable set TELEGRAM_WEBHOOK_SECRET --stdin --service "${FUNCTION_NAME}" --skip-deploys >/dev/null
printf '%s' "${TELEGRAM_CHAT_ID}" | "${RAILWAY_CMD[@]}" variable set TELEGRAM_CHAT_ID --stdin --service "${FUNCTION_NAME}" --skip-deploys >/dev/null

log "Pushing latest function code"
"${RAILWAY_CMD[@]}" functions push -p "${FUNCTION_PATH}"

log "Done. Current Railway functions:"
"${RAILWAY_CMD[@]}" functions list
