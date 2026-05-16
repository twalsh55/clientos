from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.automation.runtime import is_worker_healthy, read_heartbeat_from_file
from src.env_utils import load_env_file


def main() -> int:
    load_env_file()
    heartbeat_path = Path(os.getenv("AUTOMATION_HEARTBEAT_FILE", "var/automation_heartbeat.json"))
    payload = read_heartbeat_from_file(heartbeat_path)
    healthy = is_worker_healthy(heartbeat_path, max_age_seconds=180, now=datetime.now(tz=UTC))
    print(json.dumps({"healthy": healthy, "heartbeat": payload}, indent=2, sort_keys=True))
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
