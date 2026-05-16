from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.adapters.operator_briefing.runtime import append_product_update_note
from src.application.operator_briefing import ProductUpdateRecord
from src.env_utils import load_env_file


def main() -> int:
    load_env_file()
    parser = argparse.ArgumentParser(description="Log a product update for the daily operator briefing.")
    parser.add_argument("--category", required=True, help="feature, refinement, experiment, or similar")
    parser.add_argument("--title", required=True, help="Short title for the change")
    parser.add_argument("--summary", required=True, help="What changed")
    parser.add_argument("--agent-guidance", required=True, help="What agent guidance informed this change")
    parser.add_argument("--profitability-note", required=True, help="Why this change may improve the odds of a profitable app")
    args = parser.parse_args()

    append_product_update_note(
        ProductUpdateRecord(
            recorded_at=datetime.now(tz=UTC),
            category=args.category.strip(),
            title=args.title.strip(),
            summary=args.summary.strip(),
            agent_guidance=args.agent_guidance.strip(),
            profitability_note=args.profitability_note.strip(),
        )
    )
    print(f"Logged product update: {args.title.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
