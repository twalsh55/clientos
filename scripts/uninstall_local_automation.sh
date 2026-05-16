#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_PATH="${ROOT_DIR}/scripts/run_local_automation.py"

TMP_CRON="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${SCRIPT_PATH}" > "${TMP_CRON}" || true
crontab "${TMP_CRON}"
rm -f "${TMP_CRON}"

pkill -f "${SCRIPT_PATH}" >/dev/null 2>&1 || true

echo "Removed local automation watchdog and stopped matching worker processes."
