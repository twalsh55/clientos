from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.notifications.smtp_email_notifier import EmailNotificationError
from src.adapters.operator_briefing.runtime import (
    build_operator_briefing_config_from_env,
    collect_operator_briefing_config_errors,
    run_daily_operator_briefing_job,
)
from src.env_utils import load_env_file


def main() -> int:
    load_env_file()
    errors = collect_operator_briefing_config_errors()
    if errors:
        print("\n".join(errors))
        return 1

    try:
        config = build_operator_briefing_config_from_env()
        briefing = run_daily_operator_briefing_job()
    except (ValueError, EmailNotificationError) as exc:
        print(str(exc))
        return 1

    print(
        f"Operator briefing emailed to {config.recipient_email}. "
        f"Runs={briefing.prospect_run_count}. "
        f"Ideas={briefing.total_shortlisted_ideas}. "
        f"Updates={len(briefing.product_updates)}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
