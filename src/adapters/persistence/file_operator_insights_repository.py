from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from src.application.operator_briefing import ProductUpdateRecord, ProspectRunRecord, ShortlistedIdeaRecord
from src.domain.prospecting import ProspectTokenUsage


class FileOperatorInsightsRepository:
    def __init__(self, prospect_runs_path: Path, product_updates_path: Path) -> None:
        self.prospect_runs_path = prospect_runs_path
        self.product_updates_path = product_updates_path

    def append_prospect_run(self, run: ProspectRunRecord) -> None:
        payload = {
            "generated_at": run.generated_at.isoformat(),
            "profile": run.profile,
            "scanned_post_count": run.scanned_post_count,
            "shortlisted_count": run.shortlisted_count,
            "shortlisted_ideas": [
                {
                    "source": item.source,
                    "matched_query": item.matched_query,
                    "score": item.score,
                    "reasons": list(item.reasons),
                    "description": item.description,
                    "observed_signal": item.observed_signal,
                }
                for item in run.shortlisted_ideas
            ],
            "token_usage": (
                {
                    "model": run.token_usage.model,
                    "input_tokens": run.token_usage.input_tokens,
                    "output_tokens": run.token_usage.output_tokens,
                    "total_tokens": run.token_usage.total_tokens,
                }
                if run.token_usage is not None
                else None
            ),
        }
        self._append_jsonl(self.prospect_runs_path, payload)

    def list_prospect_runs(self, since) -> list[ProspectRunRecord]:  # type: ignore[no-untyped-def]
        runs: list[ProspectRunRecord] = []
        for payload in self._read_jsonl(self.prospect_runs_path):
            generated_at = _parse_datetime(payload.get("generated_at"))
            if generated_at is None or generated_at < since:
                continue
            runs.append(
                ProspectRunRecord(
                    generated_at=generated_at,
                    profile=str(payload.get("profile", "general")),
                    scanned_post_count=int(payload.get("scanned_post_count", 0)),
                    shortlisted_count=int(payload.get("shortlisted_count", 0)),
                    shortlisted_ideas=tuple(
                        ShortlistedIdeaRecord(
                            source=str(item.get("source", "unknown")),
                            matched_query=str(item.get("matched_query", "")),
                            score=int(item.get("score", 0)),
                            reasons=tuple(str(reason) for reason in item.get("reasons", [])),
                            description=str(item.get("description", "")),
                            observed_signal=str(item.get("observed_signal", "")),
                        )
                        for item in payload.get("shortlisted_ideas", [])
                        if isinstance(item, dict)
                    ),
                    token_usage=_parse_token_usage(payload.get("token_usage")),
                )
            )
        return sorted(runs, key=lambda item: item.generated_at)

    def append_product_update(self, update: ProductUpdateRecord) -> None:
        payload = {
            "recorded_at": update.recorded_at.isoformat(),
            "category": update.category,
            "title": update.title,
            "summary": update.summary,
            "agent_guidance": update.agent_guidance,
            "profitability_note": update.profitability_note,
        }
        self._append_jsonl(self.product_updates_path, payload)

    def list_product_updates(self, since) -> list[ProductUpdateRecord]:  # type: ignore[no-untyped-def]
        updates: list[ProductUpdateRecord] = []
        for payload in self._read_jsonl(self.product_updates_path):
            recorded_at = _parse_datetime(payload.get("recorded_at"))
            if recorded_at is None or recorded_at < since:
                continue
            updates.append(
                ProductUpdateRecord(
                    recorded_at=recorded_at,
                    category=str(payload.get("category", "update")),
                    title=str(payload.get("title", "")),
                    summary=str(payload.get("summary", "")),
                    agent_guidance=str(payload.get("agent_guidance", "")),
                    profitability_note=str(payload.get("profitability_note", "")),
                )
            )
        return sorted(updates, key=lambda item: item.recorded_at)

    def _append_jsonl(self, path: Path, payload: dict[str, object]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True))
            handle.write("\n")

    def _read_jsonl(self, path: Path) -> list[dict[str, object]]:
        if not path.exists():
            return []
        payloads: list[dict[str, object]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            decoded = json.loads(stripped)
            if isinstance(decoded, dict):
                payloads.append(decoded)
        return payloads


def _parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return datetime.fromisoformat(value)


def _parse_token_usage(value: object) -> ProspectTokenUsage | None:
    if not isinstance(value, dict):
        return None
    model = value.get("model")
    input_tokens = value.get("input_tokens")
    output_tokens = value.get("output_tokens")
    total_tokens = value.get("total_tokens")
    if not isinstance(model, str):
        return None
    if not all(isinstance(item, int) for item in (input_tokens, output_tokens, total_tokens)):
        return None
    return ProspectTokenUsage(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
    )
