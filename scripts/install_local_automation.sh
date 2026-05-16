#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/.venv/bin/python"
LOG_FILE="${ROOT_DIR}/var/local_automation.log"
SCRIPT_PATH="${ROOT_DIR}/scripts/run_local_automation.py"

mkdir -p "${ROOT_DIR}/var"

if [ ! -x "${PYTHON_BIN}" ]; then
  echo "Python virtualenv not found at ${PYTHON_BIN}" >&2
  exit 1
fi

REBOOT_LINE="@reboot cd ${ROOT_DIR} && PYTHONPATH=${ROOT_DIR} PYTHONUNBUFFERED=1 ${PYTHON_BIN} ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1"
WATCHDOG_LINE="*/5 * * * * pgrep -f '${SCRIPT_PATH}' >/dev/null || (cd ${ROOT_DIR} && PYTHONPATH=${ROOT_DIR} PYTHONUNBUFFERED=1 ${PYTHON_BIN} ${SCRIPT_PATH} >> ${LOG_FILE} 2>&1)"

TMP_CRON="$(mktemp)"
crontab -l 2>/dev/null | grep -v "${SCRIPT_PATH}" > "${TMP_CRON}" || true
{
  cat "${TMP_CRON}"
  echo "${REBOOT_LINE}"
  echo "${WATCHDOG_LINE}"
} | crontab -
rm -f "${TMP_CRON}"

if ! pgrep -f "${SCRIPT_PATH}" >/dev/null 2>&1; then
  nohup bash -lc "cd '${ROOT_DIR}' && PYTHONPATH='${ROOT_DIR}' PYTHONUNBUFFERED=1 '${PYTHON_BIN}' '${SCRIPT_PATH}' >> '${LOG_FILE}' 2>&1" >/dev/null 2>&1 &
fi

echo "Installed local automation watchdog."
crontab -l | grep "${SCRIPT_PATH}"
