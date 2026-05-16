from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.automation.runtime import run_worker_from_env
from src.env_utils import load_env_file


def main() -> int:
    load_env_file()
    try:
        return run_worker_from_env()
    except RuntimeError as exc:
        print(str(exc))
        return 1
    except ValueError as exc:
        print(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
