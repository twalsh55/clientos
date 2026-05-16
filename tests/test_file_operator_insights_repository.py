from __future__ import annotations

from datetime import UTC, datetime
import json

from src.adapters.persistence.file_operator_insights_repository import FileOperatorInsightsRepository
from src.application.operator_briefing import ProductUpdateRecord, ProspectRunRecord, ShortlistedIdeaRecord
from src.domain.prospecting import ProspectTokenUsage


def test_file_operator_insights_repository_round_trips_runs_and_updates(tmp_path) -> None:
    repository = FileOperatorInsightsRepository(
        prospect_runs_path=tmp_path / "prospect_runs.jsonl",
        product_updates_path=tmp_path / "product_updates.jsonl",
    )
    repository.append_prospect_run(
        ProspectRunRecord(
            generated_at=datetime(2026, 5, 16, 10, 0, tzinfo=UTC),
            profile="crm_direction",
            scanned_post_count=14,
            shortlisted_count=1,
            shortlisted_ideas=(
                ShortlistedIdeaRecord(
                    source="reddit",
                    matched_query="lead follow up manually",
                    score=17,
                    reasons=("mentions follow up",),
                    description="A follow-up assistant for small agencies.",
                    observed_signal="We still lose leads because follow-up is manual.",
                ),
            ),
            token_usage=ProspectTokenUsage(
                model="gpt-5-nano",
                input_tokens=100,
                output_tokens=20,
                total_tokens=120,
            ),
        )
    )
    repository.append_product_update(
        ProductUpdateRecord(
            recorded_at=datetime(2026, 5, 16, 11, 0, tzinfo=UTC),
            category="refinement",
            title="CRM scoring tune-up",
            summary="Adjusted prospect scoring toward follow-up and pipeline pain.",
            agent_guidance="The agent repeatedly highlighted manual follow-up problems.",
            profitability_note="This keeps the app pointed at recurring pain instead of broad CRM scope.",
        )
    )

    runs = repository.list_prospect_runs(datetime(2026, 5, 16, 0, 0, tzinfo=UTC))
    updates = repository.list_product_updates(datetime(2026, 5, 16, 0, 0, tzinfo=UTC))

    assert len(runs) == 1
    assert runs[0].shortlisted_ideas[0].description == "A follow-up assistant for small agencies."
    assert runs[0].token_usage is not None
    assert runs[0].token_usage.total_tokens == 120
    assert len(updates) == 1
    assert updates[0].title == "CRM scoring tune-up"


def test_file_operator_insights_repository_ignores_missing_or_old_entries(tmp_path) -> None:
    repository = FileOperatorInsightsRepository(
        prospect_runs_path=tmp_path / "prospect_runs.jsonl",
        product_updates_path=tmp_path / "product_updates.jsonl",
    )

    assert repository.list_prospect_runs(datetime(2026, 5, 16, 0, 0, tzinfo=UTC)) == []
    assert repository.list_product_updates(datetime(2026, 5, 16, 0, 0, tzinfo=UTC)) == []


def test_file_operator_insights_repository_skips_invalid_payload_shapes(tmp_path) -> None:
    prospect_runs_path = tmp_path / "prospect_runs.jsonl"
    product_updates_path = tmp_path / "product_updates.jsonl"
    prospect_runs_path.write_text(
        "\n".join(
            [
                "",
                json.dumps({"generated_at": "", "token_usage": None}),
                json.dumps(
                    {
                        "generated_at": "2026-05-16T09:00:00+00:00",
                        "profile": "crm_direction",
                        "scanned_post_count": 1,
                        "shortlisted_count": 0,
                        "shortlisted_ideas": [],
                        "token_usage": None,
                    }
                ),
                json.dumps(
                    {
                        "generated_at": "2026-05-16T10:00:00+00:00",
                        "profile": "crm_direction",
                        "scanned_post_count": 1,
                        "shortlisted_count": 1,
                        "shortlisted_ideas": ["bad"],
                        "token_usage": {"model": 1, "input_tokens": "x", "output_tokens": 1, "total_tokens": 1},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    product_updates_path.write_text(
        "\n".join(
            [
                "",
                json.dumps({"recorded_at": ""}),
                json.dumps({"recorded_at": "2026-05-16T11:00:00+00:00", "title": "Recorded"}),
                json.dumps(
                    {
                        "recorded_at": "2026-05-16T12:00:00+00:00",
                        "title": "Invalid token usage example",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    repository = FileOperatorInsightsRepository(prospect_runs_path=prospect_runs_path, product_updates_path=product_updates_path)

    runs = repository.list_prospect_runs(datetime(2026, 5, 16, 0, 0, tzinfo=UTC))
    updates = repository.list_product_updates(datetime(2026, 5, 16, 0, 0, tzinfo=UTC))

    assert len(runs) == 2
    assert runs[0].token_usage is None
    assert runs[0].shortlisted_ideas == ()
    assert len(updates) == 2
    assert updates[0].category == "update"

    prospect_runs_path.write_text(
        json.dumps(
            {
                "generated_at": "2026-05-16T13:00:00+00:00",
                "profile": "crm_direction",
                "scanned_post_count": 1,
                "shortlisted_count": 1,
                "shortlisted_ideas": [],
                "token_usage": {"model": "gpt-5-nano", "input_tokens": "x", "output_tokens": 1, "total_tokens": 1},
            }
        ),
        encoding="utf-8",
    )
    runs = repository.list_prospect_runs(datetime(2026, 5, 16, 0, 0, tzinfo=UTC))
    assert runs[0].token_usage is None
